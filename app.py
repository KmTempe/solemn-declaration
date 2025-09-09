# app.py
import os
import json
import re
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, session
from flask_session import Session
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
from mobile_validate.validator import valid_number
from redis_helper import redis_helper, cache_result, rate_limit, track_metric
from functools import wraps
import bcrypt

try:
    from mongo_helper import mongo_helper, migrate_json_to_mongo
    MONGO_AVAILABLE = True
except ImportError:
    print("MongoDB dependencies not available. Using JSON fallback.")
    MONGO_AVAILABLE = False
    mongo_helper = None

# Load .env if present
load_dotenv()

# Admin credentials (from environment)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")  # Plain password from environment
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")  # Pre-generated hash (optional)

def get_or_create_admin_hash():
    """Get admin password hash from Redis/MongoDB or generate from plain password"""
    
    # If we have a pre-generated hash, use it
    if ADMIN_PASSWORD_HASH:
        return ADMIN_PASSWORD_HASH
    
    # If we have a plain password, generate and store hash
    if ADMIN_PASSWORD:
        # Try to get existing hash from Redis first
        if redis_helper.is_available():
            stored_hash = redis_helper.get("admin:password_hash")
            if stored_hash:
                return stored_hash.decode('utf-8') if isinstance(stored_hash, bytes) else stored_hash
        
        # Generate new hash and store it
        password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Store in Redis for future use
        if redis_helper.is_available():
            redis_helper.set("admin:password_hash", password_hash, ex=86400*30)  # 30 days
            print(f"✅ Generated and stored admin password hash in Redis")
        
        # Also try to store in MongoDB if available
        if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
            try:
                mongo_helper.db.admin_config.update_one(
                    {"type": "admin_auth"},
                    {"$set": {"password_hash": password_hash, "updated_at": datetime.utcnow()}},
                    upsert=True
                )
                print(f"✅ Stored admin password hash in MongoDB")
            except Exception as e:
                print(f"⚠️ Could not store hash in MongoDB: {e}")
        
        return password_hash
    
    # Fallback to default password
    default_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print("⚠️ WARNING: Using default admin password 'admin123'. Set ADMIN_PASSWORD in production!")
    return default_hash

# Get the admin password hash (generated from plain password if needed)
CURRENT_ADMIN_HASH = get_or_create_admin_hash()

def require_admin_auth(f):
    """Decorator to require admin authentication for sensitive routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not session.get('admin_authenticated'):
            # Check for basic auth header
            auth = request.authorization
            if auth and auth.username == ADMIN_USERNAME and auth.password:
                # Verify password using bcrypt
                password_bytes = auth.password.encode('utf-8')
                hash_bytes = CURRENT_ADMIN_HASH.encode('utf-8')
                if bcrypt.checkpw(password_bytes, hash_bytes):
                    session['admin_authenticated'] = True
                    track_metric('admin_login_success')
                    return f(*args, **kwargs)
            
            track_metric('admin_login_failed')
            # Return 401 with basic auth challenge
            return jsonify({
                "error": "Authentication required",
                "message": "This endpoint requires admin authentication"
            }), 401, {'WWW-Authenticate': 'Basic realm="Admin Area"'}
        
        return f(*args, **kwargs)
    return decorated_function

# Initialize tracking system
TRACKING_FILE = "submissions_tracking.json"

def get_next_submission_id():
    """Generate next submission ID using MongoDB or JSON fallback"""
    try:
        if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
            # Use MongoDB to get next ID
            last_submission = mongo_helper.db.submissions.find_one(
                {}, 
                sort=[("submission_id", -1)]
            )
            if last_submission:
                last_id = int(last_submission.get("submission_id", "0"))
            else:
                last_id = 0
            new_id = str(last_id + 1).zfill(6)
            return new_id, {}
        else:
            # Fallback to JSON file
            if os.path.exists(TRACKING_FILE):
                with open(TRACKING_FILE, 'r') as f:
                    tracking_data = json.load(f)
                last_id = max((int(x) for x in tracking_data.keys()), default=0)
            else:
                tracking_data = {}
                last_id = 0
            
            # Generate new 6-digit ID
            new_id = str(last_id + 1).zfill(6)
            return new_id, tracking_data
    except Exception as e:
        print(f"Error managing tracking: {e}")
        return str(1).zfill(6), {}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret")

# Configure sessions with Redis (fixed implementation)
try:
    from redis_session_simple import setup_redis_sessions_simple, clear_corrupted_sessions
    
    if redis_helper.is_available():
        # Clear any corrupted session data first
        cleared_count = clear_corrupted_sessions(redis_helper.redis_client)
        if cleared_count > 0:
            print(f"🧹 Cleared {cleared_count} corrupted session keys")
        
        # Setup Redis sessions with proper configuration
        if setup_redis_sessions_simple(app, redis_helper.redis_client, clear_existing=True):
            print("✅ Using Redis for session storage with JSON serialization")
        else:
            print("⚠️ Redis session setup failed, using Flask default sessions")
    else:
        print("⚠️ Redis not available, using Flask default sessions")
        
except ImportError:
    print("⚠️ Redis session helper not found, using Flask default sessions")
except Exception as e:
    print(f"⚠️ Redis session error: {e}. Using Flask default sessions.")

# Email config - set these environment variables or edit .env
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")  # your SMTP user (email)
SMTP_PASS = os.environ.get("SMTP_PASS")  # your SMTP password or app password

# Default recipient
DEFAULT_RECIPIENT = os.environ.get("RECIPIENT_EMAIL", "level7feeders@gmail.com")

# OTP storage (fallback to in-memory if Redis unavailable)
otp_storage = {}
otp_resend_cooldown = {}

def cleanup_old_data():
    """Clean up expired OTP data and old cooldown entries"""
    current_time = datetime.now()
    
    if redis_helper.is_available():
        # Redis handles expiration automatically, just clean up fallback storage
        pass
    else:
        # Clean up expired OTPs from in-memory storage
        expired_emails = []
        for email, data in otp_storage.items():
            if current_time > data['expires_at']:
                expired_emails.append(email)
        
        for email in expired_emails:
            del otp_storage[email]
        
        # Clean up old cooldown entries (older than 1 hour)
        old_cooldowns = []
        for email, timestamp in otp_resend_cooldown.items():
            if (current_time - timestamp).total_seconds() > 3600:  # 1 hour
                old_cooldowns.append(email)
        
        for email in old_cooldowns:
            del otp_resend_cooldown[email]

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email, otp):
    """Store OTP with expiration time (5 minutes) - Redis or fallback"""
    expiration = datetime.now() + timedelta(minutes=5)
    
    if redis_helper.is_available():
        # Store in Redis with automatic expiration
        key = f"otp:{email}"
        data = {
            'otp': otp,
            'attempts': '0',
            'created_at': datetime.now().isoformat()
        }
        redis_helper.hset(key, data)
        redis_helper.expire(key, 300)  # 5 minutes
        track_metric('otp_generated')
    else:
        # Fallback to in-memory storage
        otp_storage[email] = {
            'otp': otp,
            'expires_at': expiration,
            'attempts': 0
        }

def verify_otp(email, submitted_otp):
    """Verify OTP and check if it's still valid - Redis or fallback"""
    if redis_helper.is_available():
        # Redis implementation
        key = f"otp:{email}"
        if not redis_helper.exists(key):
            return False, "OTP not found or expired"
        
        stored_otp = redis_helper.hget(key, 'otp')
        attempts_str = redis_helper.hget(key, 'attempts', '0')
        attempts = int(str(attempts_str)) if attempts_str else 0
        
        # Check if OTP matches BEFORE checking attempts
        if stored_otp == submitted_otp:
            redis_helper.delete(key)
            track_metric('otp_verified_success')
            return True, "OTP verified successfully"
        else:
            # Increment attempts after failed verification
            new_attempts = attempts + 1
            
            # Check if this failed attempt exceeds the limit
            if new_attempts >= 3:
                redis_helper.delete(key)
                track_metric('otp_too_many_attempts')
                return False, "Too many incorrect attempts"
            else:
                # Still have attempts left, update the counter
                redis_helper.hincrby(key, 'attempts', 1)
                track_metric('otp_verification_failed')
                remaining_attempts = 3 - new_attempts
                return False, f"Invalid OTP. {remaining_attempts} attempt(s) remaining"
    else:
        # Fallback to in-memory storage
        if email not in otp_storage:
            return False, "OTP not found"
        
        stored_data = otp_storage[email]
        
        # Check if OTP has expired
        if datetime.now() > stored_data['expires_at']:
            del otp_storage[email]
            return False, "OTP has expired"
        
        # Check for too many attempts
        if stored_data['attempts'] >= 3:
            del otp_storage[email]
            return False, "Too many incorrect attempts"
        
        # Check if OTP matches
        if stored_data['otp'] == submitted_otp:
            del otp_storage[email]
            return True, "OTP verified successfully"
        else:
            stored_data['attempts'] += 1
            return False, "Invalid OTP"

@cache_result("phone_validation", expiration=3600)
def validate_phone_number(phone, country="Greece"):
    """Cached phone number validation"""
    if not phone:
        return False
    try:
        return valid_number(phone, country)
    except Exception:
        return False

def send_otp_email(email, otp):
    """Send OTP to user's email"""
    subject = "Κωδικός Επαλήθευσης - Verification Code"
    body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5; max-width: 560px; margin: 0 auto; padding: 20px; color: #333;">
    <h2 style="color: #444; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Κωδικός Επαλήθευσης Email</h2>
    
    <p>Για να ολοκληρώσετε την υποβολή της φόρμας σας, παρακαλώ εισάγετε τον παρακάτω κωδικό επαλήθευσης:</p>
    
    <div style="background-color: #f5f5f5; border: 2px solid #007cba; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
        <h1 style="color: #007cba; margin: 0; font-size: 2.5em; letter-spacing: 0.2em;">{otp}</h1>
    </div>
    
    <p><strong>Σημαντικό:</strong> Αυτός ο κωδικός είναι έγκυρος για 5 λεπτά μόνο.</p>
    
    <p style="color: #666; font-size: 0.9em;">Αν δεν κάνατε αυτή την αίτηση, παρακαλώ αγνοήστε αυτό το email.</p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="color: #666; font-size: 0.8em;">Level 7 Feeders Support</p>
</body>
</html>
"""
    
    send_email(subject, body, email)
    track_metric('otp_email_sent')

# Simple utility to send email
def send_email(subject: str, body: str, recipient: str = DEFAULT_RECIPIENT, is_html: bool = True) -> None:
    msg = MIMEText(body, 'html' if is_html else 'plain', _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER or f"no-reply@{os.getenv('COMPUTERNAME', 'localhost')}"
    msg["To"] = recipient

    if not SMTP_USER or not SMTP_PASS:
        # If SMTP not configured, raise a helpful error
        raise RuntimeError("SMTP_USER and SMTP_PASS are not configured. See README / .env.example")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        if SMTP_PORT in (587, 25):
            smtp.starttls()
            smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.sendmail(msg["From"], [recipient], msg.as_string())

@app.route("/", methods=["GET", "POST"])
def index():
    # Clean up expired data periodically
    cleanup_old_data()
    
    if request.method == "GET":
        return render_template("index.html", form={}, step="form")
        
    # POST handling
    step = request.form.get("step", "form")
    
    # Rate limiting based on IP address
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if step == "form":
        # Rate limit form submissions
        if redis_helper.is_available():
            rate_key = f"rate_limit:form:{client_ip}"
            current = redis_helper.get(rate_key)
            if current is None:
                redis_helper.set(rate_key, 1, ex=3600)  # 1 hour window
            elif current and int(str(current)) >= 10:  # Max 10 submissions per hour
                flash("Πάρα πολλές προσπάθειες. Παρακαλώ δοκιμάστε αργότερα.", "error")
                return render_template("index.html", form={}, step="form")
            else:
                redis_helper.incr(rate_key)
        
        # Step 1: Process initial form and send OTP
        return handle_form_submission()
    elif step == "otp":
        # Rate limit OTP attempts
        if redis_helper.is_available():
            otp_rate_key = f"rate_limit:otp:{client_ip}"
            current = redis_helper.get(otp_rate_key)
            if current is None:
                redis_helper.set(otp_rate_key, 1, ex=300)  # 5 minute window
            elif current and int(str(current)) >= 15:  # Max 15 OTP attempts per 5 minutes
                flash("Πάρα πολλές προσπάθειες επαλήθευσης. Παρακαλώ δοκιμάστε αργότερα.", "error")
                return render_template("index.html", form={}, step="form")
            else:
                redis_helper.incr(otp_rate_key)
        
        # Step 2: Verify OTP and complete submission
        return handle_otp_verification()
    else:
        flash("Invalid request", "error")
        return redirect(url_for("index"))

def handle_form_submission():
    """Handle initial form submission and send OTP"""
    # Anti-bot honeypot (hidden field)
    honeypot = request.form.get("url_field", "")
    if honeypot:
        flash("Spam detected.", "error")
        return redirect(url_for("index"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    comments = request.form.get("comments", "").strip()

    # Basic validation
    errors = []
    if not (first_name and last_name):
        errors.append("Ονομα και Επώνυμο απαιτούνται.")
    if not email:
        errors.append("Η διεύθυνση email είναι απαραίτητη.")
    if not comments:
        errors.append("Το κείμενο της δήλωσης είναι απαραίτητο.")
    # Validate phone number format using cached validation
    if phone and not validate_phone_number(phone, "Greece"):
        errors.append("Παρακαλώ εισάγετε έγκυρο ελληνικό αριθμό τηλεφώνου +306912345678 ή +302101234567.")

    # Validate comments length
    if len(comments) > 500:
        errors.append("Τα σχόλια δεν πρέπει να υπερβαίνουν τους 500 χαρακτήρες.")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("index.html", form=request.form, step="form")

    # Store form data in session for later use
    session['form_data'] = {
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'email': email,
        'comments': comments
    }

    # Generate and send OTP
    otp = generate_otp()
    store_otp(email, otp)
    
    try:
        send_otp_email(email, otp)
        track_metric('form_to_otp_success')
        flash(f"Κωδικός επαλήθευσης στάλθηκε στο {email}. Παρακαλώ ελέγξτε το email σας.", "info")
        return render_template("index.html", form=request.form, step="otp", email=email)
    except Exception as e:
        track_metric('otp_email_failed')
        flash(f"Σφάλμα αποστολής email επαλήθευσης: {e}", "error")
        return render_template("index.html", form=request.form, step="form")

def handle_otp_verification():
    """Handle OTP verification and complete the submission"""
    email = request.form.get("email", "").strip()
    submitted_otp = request.form.get("otp", "").strip()
    
    if not email or not submitted_otp:
        flash("Παρακαλώ εισάγετε τον κωδικό επαλήθευσης.", "error")
        return render_template("index.html", form={}, step="otp", email=email)
    
    # Verify OTP
    is_valid, message = verify_otp(email, submitted_otp)
    
    if not is_valid:
        flash(f"Σφάλμα επαλήθευσης: {message}", "error")
        if "expired" in message.lower() or "too many" in message.lower():
            # OTP expired or too many attempts, redirect to form
            session.pop('form_data', None)  # Clear form data
            return render_template("index.html", form={}, step="form")
        else:
            # Invalid OTP, stay on OTP page
            return render_template("index.html", form={}, step="otp", email=email)
    
    # OTP verified, now process the original form submission
    form_data = session.get('form_data')
    if not form_data:
        flash("Τα δεδομένα της φόρμας έχουν λήξει. Παρακαλώ υποβάλετε ξανά.", "error")
        return redirect(url_for("index"))
    
    # Process the submission with stored form data
    return process_verified_submission(form_data)

def process_verified_submission(form_data):
    """Process the submission after OTP verification"""
    first_name = form_data['first_name']
    last_name = form_data['last_name']
    phone = form_data['phone']
    email = form_data['email']
    comments = form_data['comments']

    # Generate submission ID and track the submission
    submission_id, tracking_data = get_next_submission_id()
    
    # Prepare submission data for MongoDB
    submission_data = {
        "submission_id": submission_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "comments": comments,
        "name": f"{first_name} {last_name}",  # For compatibility
        "date": datetime.now().isoformat()    # For compatibility
    }
    
    # Save to MongoDB if available, otherwise use JSON fallback
    mongo_saved = False
    if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
        mongo_saved = mongo_helper.save_submission(submission_data)
        if mongo_saved:
            print(f"Submission {submission_id} saved to MongoDB")
        else:
            print(f"Failed to save submission {submission_id} to MongoDB, using JSON fallback")
    
    # Fallback to JSON file if MongoDB not available or failed
    if not mongo_saved:
        tracking_data[submission_id] = {
            "email": email,
            "name": f"{first_name} {last_name}",
            "date": datetime.now().isoformat()
        }
        try:
            with open(TRACKING_FILE, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            print(f"Submission {submission_id} saved to JSON file")
        except Exception as e:
            print(f"Error saving tracking data: {e}")
    
    # Compose email body with minimal HTML
    body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5; max-width: 560px; margin: 0 auto; padding: 20px; color: #333;">
    <h2 style="color: #444; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Νεο αιτημα επικοινωνίας</h2>
    
    <table style="width: 100%; border-spacing: 0; margin-bottom: 20px;">
        <tr><td style="padding: 8px 0;"><strong>Ονομα (First name):</strong> {first_name}</td></tr>
        <tr><td style="padding: 8px 0;"><strong>Επώνυμο (Last name):</strong> {last_name}</td></tr>
        <tr><td style="padding: 8px 0;"><strong>Τηλ. (Phone):</strong> {phone}</td></tr>
        <tr><td style="padding: 8px 0;"><strong>Email:</strong> <a href="mailto:{email}" style="color: #2b5797;">{email}</a></td></tr>
    </table>

    <div style="border: 1px solid currentColor; border-radius: 4px; padding: 15px; margin: 20px 0;">
        <div style="white-space: pre-wrap;">{comments}</div>
    </div>

    <div style="color: #666; font-size: 0.9em; margin-top: 20px;">
        Reference ID: #{submission_id}<br>
        <em>Email verified via OTP</em><br>
        <em>Storage: {'MongoDB' if mongo_saved else 'JSON File'}</em>
    </div>
</body>
</html>
"""

    subject = f"Νεο αιτημα επικοινωνίας #{submission_id} — {first_name} {last_name}"
        
    # Add submission ID to the email body
    body = f"Submission ID: #{submission_id}\n\n" + body
    
    try:
        send_email(subject, body)
        track_metric('form_submission_success')
        flash(f"Η φόρμα υποβλήθηκε επιτυχώς. Αριθμός αναφοράς: #{submission_id}", "success")
        # Clear form data from session
        session.pop('form_data', None)
    except Exception as e:
        track_metric('form_submission_failed')
        # On failure, show helpful message (do not leak credentials)
        flash(f"Σφάλμα αποστολής email: {e}", "error")
        # Optionally write to local file as fallback:
        try:
            fallback_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "submissions")
            os.makedirs(fallback_dir, exist_ok=True)
            fname = os.path.join(fallback_dir, f"comments_{first_name}_{last_name}.txt")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(body)
            flash("Η δήλωση αποθηκεύτηκε τοπικά ως fallback.", "info")
        except Exception:
            pass
        return render_template("index.html", form=form_data, step="form")

    flash("Η δήλωση στάλθηκε επιτυχώς.", "success")
    return redirect(url_for("index"))

@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    """Resend OTP to user's email with cooldown protection"""
    email = request.form.get("email", "").strip()
    
    if not email:
        flash("Η διεύθυνση email είναι απαραίτητη.", "error")
        return redirect(url_for("index"))
    
    # Check if form data exists in session
    form_data = session.get('form_data')
    if not form_data or form_data.get('email') != email:
        flash("Τα δεδομένα της φόρμας έχουν λήξει. Παρακαλώ υποβάλετε ξανά.", "error")
        return redirect(url_for("index"))
    
    # Check cooldown period (30 seconds) using Redis or fallback
    current_time = datetime.now()
    
    if redis_helper.is_available():
        cooldown_key = f"otp_resend:{email}"
        last_resend = redis_helper.get(cooldown_key)
        if last_resend:
            last_time = datetime.fromisoformat(str(last_resend))
            time_diff = (current_time - last_time).total_seconds()
            if time_diff < 30:
                remaining_time = int(30 - time_diff)
                flash(f"Παρακαλώ περιμένετε {remaining_time} δευτερόλεπτα πριν ζητήσετε νέο κωδικό.", "error")
                return render_template("index.html", form=form_data, step="otp", email=email)
        
        # Update cooldown tracker in Redis
        redis_helper.set(cooldown_key, current_time.isoformat(), ex=30)
    else:
        # Fallback to in-memory cooldown
        if email in otp_resend_cooldown:
            last_resend = otp_resend_cooldown[email]
            time_diff = (current_time - last_resend).total_seconds()
            if time_diff < 30:
                remaining_time = int(30 - time_diff)
                flash(f"Παρακαλώ περιμένετε {remaining_time} δευτερόλεπτα πριν ζητήσετε νέο κωδικό.", "error")
                return render_template("index.html", form=form_data, step="otp", email=email)
        
        # Update cooldown tracker
        otp_resend_cooldown[email] = current_time
    
    # Generate new OTP
    otp = generate_otp()
    store_otp(email, otp)
    
    try:
        send_otp_email(email, otp)
        track_metric('otp_resent')
        flash(f"Νέος κωδικός επαλήθευσης στάλθηκε στο {email}.", "info")
    except Exception as e:
        track_metric('otp_resend_failed')
        flash(f"Σφάλμα αποστολής email επαλήθευσης: {e}", "error")
    
    return render_template("index.html", form=form_data, step="otp", email=email)

@app.route("/check/<submission_id>")
def check_submission(submission_id):
    try:
        # Try MongoDB first
        if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
            submission = mongo_helper.get_submission(submission_id)
            if submission:
                return jsonify({
                    "id": submission_id,
                    "status": "found",
                    "submitted_at": submission.get("created_at", submission.get("date", "")),
                    "email": submission.get("email", ""),
                    "name": submission.get("name", f"{submission.get('first_name', '')} {submission.get('last_name', '')}").strip(),
                    "storage": "mongodb"
                })
        
        # Fallback to JSON file
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, 'r') as f:
                tracking_data = json.load(f)
            
            submission = tracking_data.get(submission_id)
            if submission:
                return jsonify({
                    "id": submission_id,
                    "status": "found",
                    "submitted_at": submission["date"],
                    "email": submission["email"],
                    "name": submission.get("name", ""),
                    "storage": "json"
                })
        
        return jsonify({"status": "not_found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/submissions")
@require_admin_auth
def view_submissions():
    """Display recent submissions (admin view)"""
    try:
        submissions = []
        storage_type = "Unknown"
        
        # Get submissions from MongoDB if available
        if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
            submissions = mongo_helper.get_recent_submissions(50)
            storage_type = "MongoDB"
        else:
            # Fallback to JSON file
            storage_type = "JSON File"
            if os.path.exists(TRACKING_FILE):
                with open(TRACKING_FILE, 'r') as f:
                    tracking_data = json.load(f)
                
                submissions = [
                    {
                        "submission_id": sub_id,
                        "email": data.get("email", ""),
                        "name": data.get("name", ""),
                        "created_at": data.get("date", ""),
                        "status": "submitted"
                    }
                    for sub_id, data in tracking_data.items()
                ]
                submissions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return jsonify({
            "submissions": submissions,
            "total": len(submissions),
            "storage": storage_type,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/metrics")
@require_admin_auth
def metrics():
    """Display application metrics (basic version)"""
    if not redis_helper.is_available():
        return jsonify({"error": "Metrics require Redis"}), 503
    
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_hour = datetime.now().strftime('%Y-%m-%d:%H')
        
        metrics_data = {
            "today": {
                "form_submissions": redis_helper.get(f"metrics:form_submission_success:{current_date}", "0"),
                "otp_generated": redis_helper.get(f"metrics:otp_generated:{current_date}", "0"),
                "otp_verified": redis_helper.get(f"metrics:otp_verified_success:{current_date}", "0"),
                "otp_failed": redis_helper.get(f"metrics:otp_verification_failed:{current_date}", "0"),
            },
            "current_hour": {
                "form_submissions": redis_helper.get(f"metrics:form_submission_success:{current_hour}", "0"),
                "otp_generated": redis_helper.get(f"metrics:otp_generated:{current_hour}", "0"),
                "otp_verified": redis_helper.get(f"metrics:otp_verified_success:{current_hour}", "0"),
                "otp_failed": redis_helper.get(f"metrics:otp_verification_failed:{current_hour}", "0"),
            },
            "redis_status": "connected",
            "mongodb_status": "connected" if (MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available()) else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add MongoDB submission counts if available
        if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
            try:
                total_submissions = mongo_helper.count_submissions()
                today_submissions = mongo_helper.count_submissions({
                    "created_at": {
                        "$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    }
                })
                metrics_data["mongodb"] = {
                    "total_submissions": total_submissions,
                    "today_submissions": today_submissions,
                    "status": "available"
                }
            except Exception as e:
                metrics_data["mongodb"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            metrics_data["mongodb"] = {
                "status": "unavailable"
            }
        
        return jsonify(metrics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Health check endpoint for production monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    overall_healthy = True
    
    # Check Redis connection
    try:
        if redis_helper.is_available() and redis_helper.redis_client:
            redis_helper.redis_client.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "sessions": "enabled",
                "caching": "enabled"
            }
        else:
            health_status["services"]["redis"] = {"status": "unavailable"}
            overall_healthy = False
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        overall_healthy = False
    
    # Check MongoDB connection
    try:
        if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
            # Try a simple operation
            mongo_helper.count_submissions()
            health_status["services"]["mongodb"] = {
                "status": "healthy",
                "storage": "enabled"
            }
        else:
            health_status["services"]["mongodb"] = {"status": "unavailable"}
            # MongoDB unavailable is not critical (we have JSON fallback)
    except Exception as e:
        health_status["services"]["mongodb"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        # MongoDB unhealthy is not critical
    
    # Check SMTP configuration
    try:
        if SMTP_USER and SMTP_PASS:
            health_status["services"]["smtp"] = {
                "status": "configured",
                "host": SMTP_HOST,
                "port": SMTP_PORT
            }
        else:
            health_status["services"]["smtp"] = {"status": "not_configured"}
            overall_healthy = False
    except Exception as e:
        health_status["services"]["smtp"] = {
            "status": "error", 
            "error": str(e)
        }
        overall_healthy = False
    
    # Set overall status
    if not overall_healthy:
        health_status["status"] = "degraded"
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_healthy else 503
    return jsonify(health_status), status_code

@app.route("/admin/logout")
@require_admin_auth 
def admin_logout():
    """Admin logout endpoint"""
    session.pop('admin_authenticated', None)
    track_metric('admin_logout')
    return jsonify({"message": "Logged out successfully"})

@app.route("/admin/password-info")
@require_admin_auth
def admin_password_info():
    """Display admin password configuration info"""
    info = {
        "username": ADMIN_USERNAME,
        "password_source": "environment" if ADMIN_PASSWORD else "hash" if ADMIN_PASSWORD_HASH else "default",
        "hash_stored_in": [],
        "hash_preview": CURRENT_ADMIN_HASH[:20] + "..." if CURRENT_ADMIN_HASH else None
    }
    
    # Check where hash is stored
    if redis_helper.is_available():
        stored_hash = redis_helper.get("admin:password_hash")
        if stored_hash:
            info["hash_stored_in"].append("Redis")
    
    if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
        try:
            stored = mongo_helper.db.admin_config.find_one({"type": "admin_auth"})
            if stored and stored.get("password_hash"):
                info["hash_stored_in"].append("MongoDB")
        except:
            pass
    
    return jsonify(info)

@app.route("/admin/regenerate-hash", methods=["POST"])
@require_admin_auth
def admin_regenerate_hash():
    """Regenerate admin password hash from current environment password"""
    global CURRENT_ADMIN_HASH
    
    if not ADMIN_PASSWORD:
        return jsonify({"error": "No ADMIN_PASSWORD set in environment"}), 400
    
    # Generate new hash
    new_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update stored hash
    CURRENT_ADMIN_HASH = new_hash
    
    # Store in Redis
    if redis_helper.is_available():
        redis_helper.set("admin:password_hash", new_hash, ex=86400*30)
    
    # Store in MongoDB
    if MONGO_AVAILABLE and mongo_helper and mongo_helper.is_available():
        try:
            mongo_helper.db.admin_config.update_one(
                {"type": "admin_auth"},
                {"$set": {"password_hash": new_hash, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            print(f"Could not update MongoDB: {e}")
    
    track_metric('admin_password_regenerated')
    return jsonify({
        "message": "Password hash regenerated successfully", 
        "hash_preview": new_hash[:20] + "..."
    })

if __name__ == "__main__":
    # For production, use gunicorn or another WSGI server.
    app.run(
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 5000)), 
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
