"""
Custom Redis Session Interface for Flask
Handles JSON serialization properly to avoid UTF-8 decode errors
"""

import json
from datetime import timedelta, datetime
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
import uuid
from typing import Any, Dict, Optional


class RedisSession(CallbackDict, SessionMixin):
    """Redis-backed session implementation"""
    
    def __init__(self, initial: Optional[Dict[str, Any]] = None, sid: Optional[str] = None, new: bool = False):
        def on_update(self):
            self.modified = True
        
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    """Custom Redis session interface with JSON serialization"""
    
    serializer = json
    session_class = RedisSession
    
    def __init__(self, redis_client, key_prefix='session:', use_signer=False):
        """
        Initialize Redis session interface
        
        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys (default: 'session:')
            use_signer: Whether to use Flask's session signer (default: False)
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.use_signer = use_signer
    
    def generate_sid(self):
        """Generate a new session ID"""
        return str(uuid.uuid4())
    
    def get_redis_key(self, sid):
        """Get Redis key for session ID"""
        return f"{self.key_prefix}{sid}"
    
    def open_session(self, app, request):
        """Load session from Redis"""
        cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        sid = request.cookies.get(cookie_name)
        
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        
        try:
            # Get session data from Redis
            redis_key = self.get_redis_key(sid)
            data = self.redis.get(redis_key)
            
            if data is not None:
                # Decode bytes to string, then parse JSON
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                data = self.serializer.loads(data)
            else:
                data = {}
                
            return self.session_class(data, sid=sid)
            
        except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
            app.logger.warning(f"Failed to load session {sid}: {e}")
            # Return new session if corrupted
            return self.session_class(sid=sid, new=True)
    
    def save_session(self, app, session, response):
        """Save session to Redis"""
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        
        # Delete session if empty
        if not session:
            if hasattr(session, 'modified') and session.modified:
                if hasattr(session, 'sid') and session.sid:
                    redis_key = self.get_redis_key(session.sid)
                    self.redis.delete(redis_key)
                response.delete_cookie(
                    cookie_name, 
                    domain=domain, 
                    path=path
                )
            return
        
        # Get cookie expiration
        cookie_exp = self.get_expiration_time(app, session)
        
        try:
            # Serialize session data to JSON
            val = self.serializer.dumps(dict(session))
            
            if hasattr(session, 'sid') and session.sid:
                redis_key = self.get_redis_key(session.sid)
                
                # Set TTL to 24 hours
                ttl = int(timedelta(days=1).total_seconds())
                self.redis.setex(redis_key, ttl, val)
                
                # Set cookie
                response.set_cookie(
                    cookie_name,
                    session.sid,
                    expires=cookie_exp,
                    httponly=self.get_cookie_httponly(app),
                    domain=domain,
                    path=path,
                    secure=self.get_cookie_secure(app)
                )
            
        except Exception as e:
            session_id = getattr(session, 'sid', 'unknown')
            app.logger.error(f"Failed to save session {session_id}: {e}")


def setup_redis_sessions(app, redis_client, key_prefix='l7form:', clear_existing=False):
    """
    Setup Redis sessions for Flask app
    
    Args:
        app: Flask application instance
        redis_client: Redis client instance
        key_prefix: Prefix for session keys
        clear_existing: Whether to clear existing session data
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Clear existing session data if requested
        if clear_existing:
            pattern = f"{key_prefix}*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                app.logger.info(f"Cleared {len(keys)} existing session keys")
        
        # Setup custom Redis session interface
        app.session_interface = RedisSessionInterface(
            redis_client=redis_client,
            key_prefix=key_prefix,
            use_signer=True
        )
        
        app.logger.info("✅ Redis session interface configured successfully")
        return True
        
    except Exception as e:
        app.logger.error(f"❌ Failed to setup Redis sessions: {e}")
        return False


def test_redis_sessions(app, redis_client):
    """
    Test Redis session functionality
    
    Args:
        app: Flask application instance
        redis_client: Redis client instance
    
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        with app.test_client() as client:
            # Test session creation
            with client.session_transaction() as sess:
                sess['test_key'] = 'test_value'
                sess['timestamp'] = datetime.now().isoformat()
            
            # Verify session was saved to Redis
            pattern = f"{app.session_interface.key_prefix}*"
            keys = redis_client.keys(pattern)
            
            if not keys:
                app.logger.error("❌ No session keys found in Redis")
                return False
            
            # Test session retrieval
            session_data = redis_client.get(keys[0])
            if session_data:
                data = json.loads(session_data.decode('utf-8'))
                if data.get('test_key') == 'test_value':
                    app.logger.info("✅ Redis session test passed")
                    
                    # Clean up test session
                    redis_client.delete(keys[0])
                    return True
            
            app.logger.error("❌ Session data validation failed")
            return False
            
    except Exception as e:
        app.logger.error(f"❌ Redis session test failed: {e}")
        return False
