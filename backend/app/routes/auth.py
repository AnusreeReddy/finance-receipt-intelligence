import datetime
import bcrypt
import jwt
from flask import Blueprint, request, jsonify, current_app
from app.models import db, User
from app.utils.validators import validate_email, validate_password
from app.utils.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not validate_email(email):
        return jsonify({'error': 'Invalid email address format'}), 400

    if not validate_password(password):
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email address is already registered'}), 409

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': new_user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    return jsonify({'message': 'Successfully logged out'}), 200