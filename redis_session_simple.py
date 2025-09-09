"""
Simple Redis Session Fix for Flask
This provides a straightforward way to re-enable Redis sessions
"""

import json
from datetime import timedelta
from flask_session import Session


def setup_redis_sessions_simple(app, redis_client, clear_existing=True):
    """
    Simple Redis session setup using Flask-Session
    
    Args:
        app: Flask application instance
        redis_client: Redis client instance
        clear_existing: Whether to clear existing session data
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Clear existing session data if requested
        if clear_existing:
            try:
                # Clear only session keys, not OTP/cache data
                pattern = "session:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
                    app.logger.info(f"Cleared {len(keys)} existing session keys")
            except Exception as e:
                app.logger.warning(f"Could not clear session keys: {e}")
        
        # Create a separate Redis connection for sessions without decode_responses
        # This is the key fix - Flask-Session 0.8.0 needs binary Redis connection
        import redis
        redis_url = redis_client.connection_pool.connection_kwargs.get('host', 'localhost')
        redis_port = redis_client.connection_pool.connection_kwargs.get('port', 6379)
        redis_db = redis_client.connection_pool.connection_kwargs.get('db', 0)
        
        # Create session Redis client without decode_responses
        session_redis = redis.Redis(
            host=redis_url, 
            port=redis_port, 
            db=redis_db,
            decode_responses=False  # Critical: Flask-Session needs binary data
        )
        
        # Test the session Redis connection
        session_redis.ping()
        
        # Configure Redis sessions with binary Redis client
        app.config.update({
            'SESSION_TYPE': 'redis',
            'SESSION_REDIS': session_redis,  # Use binary Redis client
            'SESSION_PERMANENT': False,
            'SESSION_USE_SIGNER': True,
            'SESSION_KEY_PREFIX': 'session:',
            'SESSION_COOKIE_NAME': 'l7form_session',
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SECURE': False,  # Set True for HTTPS
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=24)
        })
        
        # Initialize Flask-Session
        Session(app)
        
        app.logger.info("✅ Redis sessions configured successfully with binary Redis client")
        return True
        
    except Exception as e:
        app.logger.error(f"❌ Failed to setup Redis sessions: {e}")
        return False


def test_redis_sessions_simple(app, redis_client):
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
                sess['user_id'] = 12345
            
            # Verify session was saved to Redis
            pattern = "session:*"
            keys = redis_client.keys(pattern)
            
            if not keys:
                app.logger.error("❌ No session keys found in Redis")
                return False
            
            app.logger.info(f"✅ Found {len(keys)} session keys in Redis")
            
            # Test session retrieval in a new request
            with client.session_transaction() as sess:
                if sess.get('test_key') == 'test_value' and sess.get('user_id') == 12345:
                    app.logger.info("✅ Redis session test passed - data persisted correctly")
                    
                    # Clean up test session
                    sess.clear()
                    return True
                else:
                    app.logger.error("❌ Session data validation failed")
                    return False
            
    except Exception as e:
        app.logger.error(f"❌ Redis session test failed: {e}")
        return False


def clear_corrupted_sessions(redis_client):
    """
    Clear all corrupted session data from Redis
    
    Args:
        redis_client: Redis client instance
    
    Returns:
        int: Number of keys cleared
    """
    try:
        # Clear all session keys
        patterns = ["session:*", "l7form:*", "flask_session*"]
        total_cleared = 0
        
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                total_cleared += len(keys)
                print(f"Cleared {len(keys)} keys matching pattern: {pattern}")
        
        return total_cleared
        
    except Exception as e:
        print(f"Error clearing sessions: {e}")
        return 0


def validate_redis_connection(redis_client):
    """
    Validate Redis connection and basic operations
    
    Args:
        redis_client: Redis client instance
    
    Returns:
        bool: True if Redis is working properly
    """
    try:
        # Test basic operations
        test_key = "test:connection"
        test_value = json.dumps({"test": "data", "timestamp": "2024-01-01"})
        
        # Set and get test data
        redis_client.setex(test_key, 60, test_value)
        retrieved = redis_client.get(test_key)
        
        if retrieved:
            data = json.loads(retrieved.decode('utf-8'))
            redis_client.delete(test_key)
            
            if data.get('test') == 'data':
                print("✅ Redis connection and JSON serialization working")
                return True
        
        print("❌ Redis validation failed")
        return False
        
    except Exception as e:
        print(f"❌ Redis validation error: {e}")
        return False


if __name__ == "__main__":
    # This can be run standalone to test Redis connection
    import redis
    
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
        print("Testing Redis connection...")
        
        if validate_redis_connection(r):
            print("Redis is ready for session storage")
            cleared = clear_corrupted_sessions(r)
            print(f"Cleared {cleared} potentially corrupted session keys")
        else:
            print("Redis validation failed")
            
    except Exception as e:
        print(f"Redis connection failed: {e}")
