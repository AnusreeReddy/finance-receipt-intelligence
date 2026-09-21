import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "instance", "receipts.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Max Limit
    OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5-vl')