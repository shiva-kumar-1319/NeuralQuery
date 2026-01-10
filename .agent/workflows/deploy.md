---
description: How to deploy NeuralQuery to production
---

# Deployment Workflow

This workflow guides you through the process of deploying NeuralQuery.

## 1. Cleanup
Ensure all temporary files are removed:
// turbo
```powershell
del *.pyc
del __pycache__ -Recurse -Force
```

## 2. Environment Configuration
Check if `.env` exists and has production values:
```powershell
ls .env
```

## 3. Install Production Dependencies
// turbo
```powershell
pip install -r requirements.txt
```

## 4. Run Production Server
// turbo
```powershell
python run_production.py
```

For cloud platforms like Render or Heroku, ensure your environment variables (GEMINI_API_KEY, etc.) are set in their dashboard.
