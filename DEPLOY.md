# Deployment Guide - NeuralQuery

This guide provides steps to deploy NeuralQuery in a production environment.

## 1. Environment Configuration

Create a `.env` file in the root directory with production values:

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_key
NEWS_API_KEY=your_newsapi_key

# Security (CRITICAL: Change these to long random strings)
JWT_SECRET=your_production_long_random_secret_key

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# App Settings
FLASK_ENV=production
FLASK_DEBUG=False
```

## 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## 3. Running in Production (Windows)

On Windows, we use `Waitress` as the production WSGI server.

```bash
python run_production.py
```

The server will be available at `http://localhost:5000` (or whatever port you specify via `PORT` env var).

## 4. Security Checklist

- [ ] `FLASK_ENV` is set to `production`.
- [ ] `FLASK_DEBUG` is set to `False`.
- [ ] `JWT_SECRET` is NOT the default development value.
- [ ] All API keys are valid.
- [ ] CORS origins are restricted to your actual frontend domain if hosted separately.
