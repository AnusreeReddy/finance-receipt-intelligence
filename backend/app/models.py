from datetime import datetime
from app import db  # <--- MUST import from app, DO NOT call SQLAlchemy() here

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    receipts = db.relationship('Receipt', backref='owner', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class Receipt(db.Model):
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    merchant_name = db.Column(db.String(255), nullable=True)
    receipt_date = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Float, nullable=True)
    tax = db.Column(db.Float, nullable=True)
    total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), default='Uncategorized')
    image_path = db.Column(db.String(512), nullable=False)
    raw_ocr_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='PENDING_REVIEW')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'merchant_name': self.merchant_name,
            'receipt_date': self.receipt_date.isoformat() if self.receipt_date else None,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'total': self.total,
            'payment_method': self.payment_method,
            'category': self.category,
            'image_path': self.image_path,
            'raw_ocr_text': self.raw_ocr_text,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ReceiptItem(db.Model):
    __tablename__ = 'receipt_items'

    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id', ondelete='CASCADE'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'price': self.price
        }