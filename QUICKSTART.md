# 🚀 Quick Start Guide for NeuralQuery Backend

## ⚡ 5-Minute Setup

### Step 1: Get Gemini API Key (FREE)

1. Go to [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### Step 2: Configure Environment

Open `.env` file and add your API key:

```env
GEMINI_API_KEY=AIzaSy...your_api_key_here
```

**Important**: Keep the rest of the `.env` file as is for now (PostgreSQL setup is optional for testing).

### Step 3: Install PostgreSQL (if not installed)

**Windows:**
```bash
# Download from: https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql

# Verify:
psql --version
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

### Step 4: Create Database

```bash
# Windows (PowerShell as Administrator):
& 'C:\Program Files\PostgreSQL\16\bin\psql.exe' -U postgres
# Enter password when prompted (default: postgres)

# Then in psql:
CREATE DATABASE neuralquery;
\q
```

**If you don't want to setup PostgreSQL**, you can use SQLite temporarily:

Change `.env`:
```env
DATABASE_URL=sqlite:///neuralquery.db
```

And modify `requirements.txt` to remove `psycopg2-binary`.

### Step 5: Verify Setup

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run verification
python verify_setup.py
```

### Step 6: Initialize Database

```bash
# Method 1: Using Python
python models.py

# Method 2: Using SQL script (PostgreSQL only)
psql -U postgres -d neuralquery -f schema.sql
```

### Step 7: Create Test Users (Optional)

```bash
python create_test_users.py
```

This creates 50 test users with emails `user1@test.com` through `user50@test.com`, all with password `test123`.

### Step 8: Start the Server

```bash
python app.py
```

You should see:
```
🧠 NeuralQuery - AI Research Assistant
============================================================
📍 Environment: development
🔧 Debug Mode: True
============================================================
✅ Database initialized

 * Running on http://0.0.0.0:5000
```

### Step 9: Test the API

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

**Register a User:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"demo@test.com\",\"password\":\"demo123\",\"full_name\":\"Demo User\"}"
```

You should get a response with a JWT token!

**Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"demo@test.com\",\"password\":\"demo123\"}"
```

**Test AI Research** (replace `<TOKEN>` with your JWT from login):
```bash
curl -X POST http://localhost:5000/api/research \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d "{\"query\":\"latest developments in AI 2026\"}"
```

## 🐛 Common Issues

### Issue: "No module named 'flask'"
**Solution:**
```bash
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "psycopg2" installation fails on Windows
**Solution:**
Use the binary version (already in requirements.txt):
```bash
pip install psycopg2-binary
```

### Issue: "could not connect to database"
**Solution:**
1. Make sure PostgreSQL is running
2. Check your `DATABASE_URL` in `.env`
3. Try: `psql -U postgres` to verify connection

### Issue: "GEMINI_API_KEY is required"
**Solution:**
1. Get API key from https://makersuite.google.com/app/apikey
2. Add it to `.env` file
3. Restart the server

### Issue: DuckDuckGo search timeout
**Solution:**
- Check your internet connection
- Try running a simple search test:
```python
from duckduckgo_search import DDGS
results = DDGS().text("test", max_results=5)
print(results)
```

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL installed and running
- [ ] Database created (`neuralquery`)
- [ ] Gemini API key added to `.env`
- [ ] Database schema initialized
- [ ] Server starts without errors
- [ ] Health check returns 200 OK
- [ ] Can register and login users
- [ ] AI research endpoint works

## 🎯 Ready to Code!

Once all checks pass, you're ready to:
1. Test all API endpoints
2. Build the frontend
3. Deploy to production

## 📚 Next Steps

1. Review `README.md` for full documentation
2. Check `app.py` for all available endpoints
3. Read code comments for implementation details
4. Start building the frontend!

---

**Need help?** Check the main README.md or create an issue on GitHub.
