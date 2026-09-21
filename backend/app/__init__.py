import os
from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    # Get the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))  # /backend/app
    backend_parent = os.path.dirname(backend_dir)  # /backend
    project_root = os.path.dirname(backend_parent)  # /
    
    app = Flask(__name__)
    
    # Configurations
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-12345')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///finance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(backend_parent, 'uploads')

    db.init_app(app)
    CORS(app)

    # Health Check Route
    @app.route('/', methods=['GET'])
    def health_check():
        return jsonify({"status": "online", "message": "Finance Tracker API is running"}), 200
    
    # Frontend routes
    @app.route('/frontend/<path:filename>')
    def serve_frontend(filename):
        """Serve frontend HTML files"""
        frontend_path = os.path.join(project_root, 'frontend')
        return send_from_directory(frontend_path, filename)
    
    @app.route('/frontend/')
    def frontend_index():
        """Redirect to login page"""
        frontend_path = os.path.join(project_root, 'frontend')
        return send_from_directory(frontend_path, 'login.html')

    # Register Blueprints
    from app.routes.receipts import receipts_bp
    from app.routes.auth import auth_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(receipts_bp, url_prefix='/api/receipts')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    with app.app_context():
        db.create_all()

    return app