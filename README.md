# 🧠 NeuralQuery - AI Research Assistant

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

> **Professional Portfolio Project** - An AI-powered research assistant with ChatGPT-like interface, demonstrating full-stack development, AI integration, and clean code practices.

## ✨ Features

- 🔐 **User Authentication** - Secure registration/login with JWT tokens and bcrypt password hashing
- 🔍 **AI Research** - Multi-source web search using DuckDuckGo API (legal & free)
- 🤖 **AI Analysis** - Google Gemini integration for intelligent content synthesis
- 📊 **Accuracy Metrics** - Comprehensive accuracy scoring based on source quality, freshness, and consensus
- 📁 **File Upload** - Upload and analyze PDF, DOC, DOCX, and TXT documents
- 💬 **Conversation History** - Save and manage research conversations
- 🎨 **Modern UI** - ChatGPT-style interface (frontend in progress)

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens + bcrypt
- **AI**: Google Gemini API
- **Search**: DuckDuckGo Search API (no API key needed!)
- **Web Scraping**: BeautifulSoup4 + Requests

### Frontend (Coming Soon)
- **Structure**: HTML5 semantic markup
- **Styling**: Vanilla CSS with modern design
- **Logic**: Pure JavaScript (no frameworks)

## 📋 Prerequisites

- Python 3.8+ (tested with 3.12)
- PostgreSQL 12+ installed and running
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/neuralquery.git
cd neuralquery

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/neuralquery

# AI API
GEMINI_API_KEY=your_gemini_api_key_here

# Security
JWT_SECRET=your_super_secret_jwt_key_change_in_production

# Flask
FLASK_ENV=development
FLASK_DEBUG=True

# File Uploads
UPLOAD_FOLDER=./uploads
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,doc,docx,txt

# CORS
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb neuralquery

# Or using psql:
psql -U postgres
CREATE DATABASE neuralquery;
\q

# Initialize database schema
psql -U postgres -d neuralquery -f schema.sql

# OR initialize using Python:
python models.py
```

### 4. Create Test Users (Optional)

```bash
# Create 50 test users with sample conversations
python create_test_users.py

# Or create a custom number:
python create_test_users.py 10
```

**Test User Credentials:**
- Email: `user1@test.com` through `user50@test.com`  
- Password: `test123`

### 5. Run the Application

```bash
# Start the Flask server
python app.py

# Server will start on http://localhost:5000
```

## 📡 API Endpoints

### Authentication

#### Register New User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### Research

#### Perform AI Research
```http
POST /api/research
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What are the latest developments in artificial intelligence?",
  "conversation_id": 123  // optional
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on recent sources, here are the key developments in AI...",
  "accuracy": {
    "overall_accuracy": 85,
    "confidence_level": "High",
    "sources_analyzed": 8,
    "verified_count": 7,
    "latest_source_date": "2 days ago"
  },
  "sources": [...],
  "conversation_id": 123,
  "message_id": 456
}
```

### Conversations

#### Get All Conversations
```http
GET /api/conversations
Authorization: Bearer <token>
```

#### Get Specific Conversation
```http
GET /api/conversations/<id>
Authorization: Bearer <token>
```

#### Delete Conversation
```http
DELETE /api/conversations/<id>
Authorization: Bearer <token>
```

### File Upload

#### Upload File
```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
```

#### Analyze Uploaded File
```http
POST /api/analyze-file
Authorization: Bearer <token>
Content-Type: application/json

{
  "file_text": "extracted text from file...",
  "query": "Summarize this document",
  "conversation_id": 123
}
```

### Health Check
```http
GET /api/health
```

## 🧪 Testing

### Manual Testing with cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Research (replace <TOKEN> with your JWT)
curl -X POST http://localhost:5000/api/research \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"query":"latest AI trends 2026"}'
```

### Testing with Postman

1. Import the API endpoints
2. Set Authorization header: `Bearer <your_token>`
3. Test each endpoint

## 📁 Project Structure

```
neuralquery/
├── app.py                    # Main Flask application
├── config.py                 # Configuration management
├── models.py                 # Database models (SQLAlchemy)
├── auth.py                   # Authentication & JWT
├── research.py               # DuckDuckGo search + AI analysis
├── accuracy.py               # Accuracy calculation logic
├── requirements.txt          # Python dependencies
├── schema.sql               # PostgreSQL database schema
├── create_test_users.py     # Test data generation
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── static/
│   ├── css/
│   │   └── style.css        # CSS styling
│   └── js/
│       └── main.js          # JavaScript logic
├── templates/
│   ├── landing.html         # Landing page
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   └── chat.html            # Chat interface
└── uploads/                 # Uploaded files storage
```

## 🔒 Security Features

- ✅ **Password Hashing**: bcrypt with 12 rounds
- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- ✅ **XSS Prevention**: Input sanitization
- ✅ **File Upload Validation**: Type and size checks
- ✅ **CORS Configuration**: Controlled origins
- ✅ **HTTPS Ready**: Production-ready configuration

## 🌐 Deployment

### Option 1: Railway (Recommended)

1. Create account on [Railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL plugin
4. Deploy from GitHub
5. Set environment variables
6. Deploy!

### Option 2: Render

1. Create account on [Render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repository
4. Add PostgreSQL database
5. Set environment variables
6. Deploy

### Option 3: Heroku

1. Install Heroku CLI
2. Create Heroku app: `heroku create neuralquery`
3. Add PostgreSQL: `heroku addons:create heroku-postgresql:mini`
4. Set environment variables: `heroku config:set GEMINI_API_KEY=...`
5. Deploy: `git push heroku main`

### Production Checklist

- [ ] Change `JWT_SECRET` to strong random value
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Add rate limiting (optional)

## 🐛 Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Ensure PostgreSQL is running and `DATABASE_URL` in `.env` is correct.

### Gemini API Error

```
google.generativeai.types.generation_types.BlockedPromptException
```

**Solution**: Check your API key and ensure it's valid.

### DuckDuckGo Search Timeout

```
requests.exceptions.Timeout
```

**Solution**: Check your internet connection. DuckDuckGo search is free and doesn't require authentication.

### Import Error

```
ModuleNotFoundError: No module named 'flask'
```

**Solution**: Activate virtual environment and run `pip install -r requirements.txt`

## 💡 Key Technical Highlights for Resume

✨ Things that make this project impressive:

1. **Legal API Integration**: Uses DuckDuckGo search API (not illegal Google scraping)
2. **Clean Architecture**: Separation of concerns (models, auth, research, accuracy)
3. **Security Best Practices**: JWT, bcrypt, input validation, SQL injection prevention
4. **AI Integration**: Google Gemini for intelligent content synthesis
5. **Scalable Database Design**: PostgreSQL with proper relationships and indexes
6. **RESTful API**: Well-designed endpoints following REST principles
7. **Professional Documentation**: Comprehensive README and inline comments
8. **Error Handling**: Graceful error handling throughout
9. **Type Hints**: Python type hints for better code maintainability
10. **Production Ready**: Environment-based configuration, HTTPS ready

## 📝 License

MIT License - see LICENSE file for details

## 👤 Author

**Your Name**
- Portfolio: [yourportfolio.com](https://yourportfolio.com)
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Name](https://linkedin.com/in/yourname)

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- DuckDuckGo for free, legal search API
- Flask community for excellent documentation

---

**Note**: This is a portfolio/educational project demonstrating full-stack development skills. Not intended for production use without proper security audits and scaling considerations.

**For Recruiters**: This project demonstrates proficiency in:
- Backend development (Python/Flask)
- Database design (PostgreSQL/SQLAlchemy)
- API integration (AI, Search)
- Authentication & Security
- RESTful API design
- Clean code practices
- Professional documentation
