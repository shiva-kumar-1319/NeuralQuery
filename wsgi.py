from app import app
from models import init_db

# Initialize database before serving
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run()
