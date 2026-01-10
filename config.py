"""
Configuration management for NeuralQuery application.
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Application configuration class.
    All settings are loaded from environment variables.
    """
    
    # Database Configuration
    _raw_db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/neuralquery')
    # Handle Render/Heroku providing postgres:// instead of postgresql://
    DATABASE_URL = _raw_db_url.replace('postgres://', 'postgresql://') if _raw_db_url else _raw_db_url
    
    # AI API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    
    # Security Settings
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    # Flask Settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('JWT_SECRET') # No default in production for security
    
    @staticmethod
    def get_jwt_secret():
        secret = os.getenv('JWT_SECRET')
        if not secret:
            if Config.FLASK_ENV == 'production':
                raise ValueError("JWT_SECRET must be set in environment for production!")
            return 'dev-secret-change-in-production'
        return secret
    
    # File Upload Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 10485760))  # 10MB default
    ALLOWED_EXTENSIONS = set(
        os.getenv('ALLOWED_EXTENSIONS', 'pdf,doc,docx,txt').split(',')
    )
    
    # CORS Settings
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS', 
        'http://localhost:5000,http://127.0.0.1:5000'
    ).split(',')
    
    # Search Settings (DuckDuckGo - no API key needed!)
    SEARCH_MAX_RESULTS = 10  # Number of search results to fetch
    SEARCH_TIMEOUT = 10  # Timeout for search requests in seconds
    
    # Content Fetching Settings
    REQUEST_TIMEOUT = 10  # Timeout for web requests in seconds
    REQUEST_DELAY = 1  # Delay between requests in seconds (be respectful)
    USER_AGENT = 'NeuralQuery/1.0 (Educational Research Assistant)'
    
    # AI Settings
    AI_MAX_TOKENS = 2048  # Maximum tokens for AI response
    AI_TEMPERATURE = 0.7  # AI response creativity (0.0 - 1.0)
    AI_REQUEST_TIMEOUT = 120  # Timeout for AI requests in seconds
    AI_DEFAULT_MODEL = 'models/gemini-2.0-flash'  # Verified to exist
    
    @staticmethod
    def validate():
        """
        Validate required configuration settings.
        Raises an exception if critical settings are missing.
        """
        if not Config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is required. "
                "Get your API key from https://makersuite.google.com/app/apikey"
            )
        
        if Config.JWT_SECRET == 'dev-secret-change-in-production' and \
           Config.FLASK_ENV == 'production':
            raise ValueError(
                "JWT_SECRET must be changed in production environment"
            )
        
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        return True


# Validate configuration on import (except during testing)
if os.getenv('TESTING') != 'True':
    try:
        Config.validate()
    except ValueError as e:
        print(f"⚠️  Configuration Warning: {e}")
