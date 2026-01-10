"""
Authentication utilities for NeuralQuery application.
Handles JWT token generation, validation, and route protection.
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import jwt

from config import Config


def generate_token(user_id: int) -> str:
    """
    Generate JWT token for authenticated user.
    
    Args:
        user_id: User's database ID
        
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    return token


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def require_auth(f):
    """
    Decorator to protect routes that require authentication.
    Validates JWT token from Authorization header.
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route(current_user_id):
            # current_user_id is automatically passed
            return {'message': 'Success'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'No authorization header provided'
            }), 401
        
        # Extract token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header format. Use: Bearer <token>'
            }), 401
        
        # Validate token
        try:
            payload = decode_token(token)
            current_user_id = payload['user_id']
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 401
        
        # Pass user_id to the route function
        return f(current_user_id, *args, **kwargs)
    
    return decorated_function


def extract_user_id_from_request() -> int:
    """
    Extract user ID from current request's JWT token.
    Use this in routes that are already protected by @require_auth.
    
    Returns:
        User ID from token
        
    Raises:
        ValueError: If token is invalid or missing
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        raise ValueError("No authorization header")
    
    try:
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        return payload['user_id']
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid token: {e}")


# Security helper functions

def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no directory traversal attacks).
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if safe, False otherwise
    """
    # Block path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Block hidden files
    if filename.startswith('.'):
        return False
    
    return True


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed for upload.
    
    Args:
        filename: Name of file to check
        
    Returns:
        True if extension is allowed, False otherwise
    """
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in Config.ALLOWED_EXTENSIONS


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text
