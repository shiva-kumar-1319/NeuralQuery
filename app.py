"""
NeuralQuery - AI-Powered Research Assistant
Main Flask Application

This is the core Flask application that handles all API endpoints.
Author: Portfolio Project for Resume
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from config import Config
from models import get_db, User, Conversation, Message, UploadedFile, init_db
from auth import generate_token, require_auth, allowed_file, sanitize_input, is_safe_filename
from research import perform_research
import PyPDF2
import docx

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE

# Configure CORS
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


# ============================================================================
# STATIC FILE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve landing page"""
    return send_from_directory('templates', 'landing.html')


@app.route('/login')
def login_page():
    """Serve login page"""
    return send_from_directory('templates', 'login.html')


@app.route('/register')
def register_page():
    """Serve registration page"""
    return send_from_directory('templates', 'register.html')


@app.route('/chat')
def chat_page():
    """Serve chat interface"""
    return send_from_directory('templates', 'chat.html')


@app.route('/admin')
def admin_page():
    """Serve admin dashboard"""
    return send_from_directory('templates', 'admin.html')


# ============================================================================
# AUTHENTICATION API ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "password123",
            "full_name": "John Doe"
        }
    
    Response:
        {
            "success": true,
            "message": "User registered successfully",
            "token": "jwt_token_here",
            "user": {...}
        }
    """
    try:
        data = request.get_json()
        
        # Validate input
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = sanitize_input(data.get('full_name', ''))
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        # Check if user already exists
        db = next(get_db())
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400
        
        # Create new user
        new_user = User(
            email=email,
            full_name=full_name
        )
        new_user.set_password(password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate JWT token
        token = generate_token(new_user.id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({
            'success': False,
            'error': 'Registration failed'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
    
    Response:
        {
            "success": true,
            "token": "jwt_token_here",
            "user": {...}
        }
    """
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Find user
        db = next(get_db())
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not user.verify_password(password):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Generate JWT token
        token = generate_token(user.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500


# ============================================================================
# RESEARCH API ENDPOINTS
# ============================================================================

@app.route('/api/research', methods=['POST'])
@require_auth
def research(current_user_id):
    """
    Perform AI research on a query.
    
    Headers:
        Authorization: Bearer <token>
    
    Request Body:
        {
            "query": "What are the latest AI developments?",
            "conversation_id": 123  // optional, creates new if not provided
        }
    
    Response:
        {
            "success": true,
            "response": "AI-generated analysis...",
            "accuracy": {...},
            "sources": [...],
            "conversation_id": 123,
            "message_id": 456
        }
    """
    try:
        data = request.get_json()
        query = sanitize_input(data.get('query', ''), max_length=1000)
        conversation_id = data.get('conversation_id')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Get database session
        db = next(get_db())
        
        # Create or get conversation
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user_id
            ).first()
            
            if not conversation:
                return jsonify({
                    'success': False,
                    'error': 'Conversation not found'
                }), 404
        else:
            # Create new conversation
            conversation = Conversation(
                user_id=current_user_id,
                title=query[:100]  # First 100 chars as title
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role='user',
            content=query
        )
        db.add(user_message)
        db.commit()
        
        # Perform research
        print(f"🔬 User {current_user_id} researching: {query}")
        research_result = perform_research(query)
        
        if not research_result['success']:
            return jsonify({
                'success': False,
                'error': research_result.get('error', 'Research failed')
            }), 500
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=research_result['response'],
            accuracy_score=research_result['accuracy'].get('overall_accuracy'),
            sources_count=research_result['accuracy'].get('sources_analyzed')
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return jsonify({
            'success': True,
            'response': research_result['response'],
            'accuracy': research_result['accuracy'],
            'sources': research_result['sources'],
            'conversation_id': conversation.id,
            'message_id': assistant_message.id
        }), 200
        
    except Exception as e:
        print(f"❌ Research endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Research failed'
        }), 500


# ============================================================================
# CONVERSATION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/conversations', methods=['GET'])
@require_auth
def get_conversations(current_user_id):
    """
    Get all conversations for the current user.
    
    Response:
        {
            "success": true,
            "conversations": [
                {
                    "id": 123,
                    "title": "Latest AI developments",
                    "created_at": "2026-01-07T...",
                    "message_count": 4
                },
                ...
            ]
        }
    """
    try:
        db = next(get_db())
        
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user_id
        ).order_by(Conversation.updated_at.desc()).all()
        
        return jsonify({
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        }), 200
        
    except Exception as e:
        print(f"❌ Get conversations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch conversations'
        }), 500


@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@require_auth
def get_conversation(current_user_id, conversation_id):
    """
    Get a specific conversation with all messages.
    
    Response:
        {
            "success": true,
            "conversation": {...},
            "messages": [...]
        }
    """
    try:
        db = next(get_db())
        
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user_id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict(include_messages=True)
        }), 200
        
    except Exception as e:
        print(f"❌ Get conversation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch conversation'
        }), 500


@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(current_user_id, conversation_id):
    """
    Delete a conversation and all its messages.
    
    Response:
        {
            "success": true,
            "message": "Conversation deleted"
        }
    """
    try:
        db = next(get_db())
        
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user_id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        db.delete(conversation)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conversation deleted'
        }), 200
        
    except Exception as e:
        print(f"❌ Delete conversation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete conversation'
        }), 500


# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ''


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return ''


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"TXT extraction error: {e}")
        return ''


@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file(current_user_id):
    """
    Upload a file for analysis.
    
    Response:
        {
            "success": true,
            "file_id": 123,
            "filename": "document.pdf",
            "extracted_text": "..."
        }
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        if not is_safe_filename(filename):
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{current_user_id}_{timestamp}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Extract text based on file type
        extension = filename.rsplit('.', 1)[1].lower()
        
        if extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif extension in ['doc', 'docx']:
            extracted_text = extract_text_from_docx(file_path)
        elif extension == 'txt':
            extracted_text = extract_text_from_txt(file_path)
        else:
            extracted_text = ''
        
        # Save to database
        db = next(get_db())
        uploaded_file = UploadedFile(
            user_id=current_user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size
        )
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        
        return jsonify({
            'success': True,
            'file_id': uploaded_file.id,
            'filename': filename,
            'extracted_text': extracted_text[:5000]  # Limit to 5000 chars
        }), 200
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({
            'success': False,
            'error': 'File upload failed'
        }), 500


@app.route('/api/analyze-file', methods=['POST'])
@require_auth
def analyze_file(current_user_id):
    """
    Analyze an uploaded file with a query.
    
    Request Body:
        {
            "file_text": "extracted text from file...",
            "query": "What is this document about?",
            "conversation_id": 123  // optional
        }
    """
    try:
        data = request.get_json()
        
        file_text = sanitize_input(data.get('file_text', ''), max_length=50000)
        query = sanitize_input(data.get('query', ''), max_length=1000)
        conversation_id = data.get('conversation_id')
        
        if not file_text or not query:
            return jsonify({
                'success': False,
                'error': 'File text and query are required'
            }), 400
        
        # Create mock source from file
        sources = [{
            'url': 'Uploaded Document',
            'title': 'User Uploaded File',
            'snippet': file_text[:500],
            'content': file_text
        }]
        
        # Use AI analysis
        from research import analyze_with_ai, calculate_accuracy
        
        ai_response = analyze_with_ai(query, sources)
        accuracy_metrics = calculate_accuracy(sources, ai_response)
        
        # Save to database if conversation_id provided
        if conversation_id:
            db = next(get_db())
            
            user_message = Message(
                conversation_id=conversation_id,
                role='user',
                content=f"[File Analysis] {query}"
            )
            db.add(user_message)
            
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=ai_response,
                accuracy_score=accuracy_metrics.get('overall_accuracy'),
                sources_count=1
            )
            db.add(assistant_message)
            db.commit()
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'accuracy': accuracy_metrics
        }), 200
        
    except Exception as e:
        print(f"❌ File analysis error: {e}")
        return jsonify({
            'success': False,
            'error': 'File analysis failed'
        }), 500


# ============================================================================
# ADMIN API ENDPOINTS
# ============================================================================

@app.route('/api/admin/users', methods=['GET'])
@require_auth
def get_admin_users(current_user_id):
    """
    Get all users with their chat counts.
    Simple administration view.
    """
    try:
        db = next(get_db())
        
        # In a real app, we would check if current_user_id is an actual admin
        # For now, we allow any authenticated user to view the list as requested
        
        users = db.query(User).all()
        user_list = []
        
        for user in users:
            chat_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
            user_data = user.to_dict()
            user_data['chat_count'] = chat_count
            user_list.append(user_data)
            
        return jsonify({
            'success': True,
            'users': user_list
        })
    except Exception as e:
        print(f"❌ Admin API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Response:
        {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2026-01-07T..."
        }
    """
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {Config.MAX_UPLOAD_SIZE // 1024 // 1024}MB'
    }), 413


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧠 NeuralQuery - AI Research Assistant")
    print("="*60)
    print(f"📍 Environment: {Config.FLASK_ENV}")
    print(f"🔧 Debug Mode: {Config.DEBUG}")
    print(f"🌐 CORS Origins: {', '.join(Config.CORS_ORIGINS)}")
    print("="*60 + "\n")
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized\n")
    except Exception as e:
        print(f"⚠️  Database warning: {e}\n")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
