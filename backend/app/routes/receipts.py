import os
import werkzeug.utils
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory

from app import db
from app.models import Receipt, ReceiptItem, User
from app.utils.auth_middleware import token_required
from app.services.image_processor import ImageProcessor
from app.services.ocr_engine import OCREngine
from app.services.llm_parser import LLMParser
from app.services.ml_model import MLModel
from app.services.database import save_receipt


receipts_bp = Blueprint('receipts', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


ocr_engine = OCREngine()


@receipts_bp.route('/', methods=['GET'], strict_slashes=False)
@token_required
def get_user_receipts(current_user):
    """Get all receipts for the current user with optional filtering"""
    try:
        query = Receipt.query.filter_by(user_id=current_user.id)

        # Apply filters
        search = request.args.get('search', '').strip()
        if search:
            query = query.filter(Receipt.merchant_name.ilike(f'%{search}%'))

        category = request.args.get('category', '').strip()
        if category and category != 'All':
            query = query.filter_by(category=category)

        start_date = request.args.get('start_date', '').strip()
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Receipt.receipt_date >= start_date_obj)
            except:
                pass

        end_date = request.args.get('end_date', '').strip()
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Receipt.receipt_date <= end_date_obj)
            except:
                pass

        receipts = query.order_by(Receipt.receipt_date.desc()).all()

        return jsonify({
            'receipts': [r.to_dict() for r in receipts]
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch receipts: {str(e)}"
        }), 500


@receipts_bp.route('/<int:receipt_id>', methods=['GET'])
@token_required
def get_receipt(current_user, receipt_id):
    """Get a single receipt by ID"""
    try:
        receipt = Receipt.query.filter_by(
            id=receipt_id,
            user_id=current_user.id
        ).first()

        if not receipt:
            return jsonify({"error": "Receipt not found"}), 404

        return jsonify({
            'receipt': receipt.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch receipt: {str(e)}"
        }), 500


@receipts_bp.route('/<int:receipt_id>', methods=['PUT'])
@token_required
def update_receipt(current_user, receipt_id):
    """Update receipt details"""
    try:
        receipt = Receipt.query.filter_by(
            id=receipt_id,
            user_id=current_user.id
        ).first()

        if not receipt:
            return jsonify({"error": "Receipt not found"}), 404

        data = request.get_json() or {}

        # Validate and update fields
        if 'merchant_name' in data:
            receipt.merchant_name = str(
                data['merchant_name']
            ).strip() or 'Unknown Store'

        if 'receipt_date' in data and data['receipt_date']:
            try:
                receipt.receipt_date = datetime.strptime(
                    str(data['receipt_date']),
                    '%Y-%m-%d'
                ).date()
            except:
                return jsonify({
                    "error": "Invalid date format. Use YYYY-MM-DD"
                }), 400

        if 'category' in data:
            receipt.category = str(
                data['category']
            ).strip() or 'Other'

        if 'payment_method' in data:
            receipt.payment_method = str(
                data['payment_method']
            ).strip() or 'Other'

        if 'subtotal' in data:
            try:
                receipt.subtotal = (
                    float(data['subtotal'])
                    if data['subtotal']
                    else 0.0
                )
            except:
                return jsonify({
                    "error": "Invalid subtotal amount"
                }), 400

        if 'tax' in data:
            try:
                receipt.tax = (
                    float(data['tax'])
                    if data['tax']
                    else 0.0
                )
            except:
                return jsonify({
                    "error": "Invalid tax amount"
                }), 400

        if 'total' in data:
            try:
                total_val = float(data['total'])

                if total_val < 0:
                    return jsonify({
                        "error": "Total amount cannot be negative"
                    }), 400

                receipt.total = total_val

            except:
                return jsonify({
                    "error": "Invalid total amount"
                }), 400

        receipt.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Receipt updated successfully',
            'receipt': receipt.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": f"Failed to update receipt: {str(e)}"
        }), 500


@receipts_bp.route('/<int:receipt_id>', methods=['DELETE'])
@token_required
def delete_receipt(current_user, receipt_id):
    """Delete a receipt"""
    try:
        receipt = Receipt.query.filter_by(
            id=receipt_id,
            user_id=current_user.id
        ).first()

        if not receipt:
            return jsonify({"error": "Receipt not found"}), 404

        # Delete associated image file
        if receipt.image_path and os.path.exists(receipt.image_path):
            try:
                os.remove(receipt.image_path)
            except:
                pass

        db.session.delete(receipt)
        db.session.commit()

        return jsonify({
            'message': 'Receipt deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": f"Failed to delete receipt: {str(e)}"
        }), 500


@receipts_bp.route('/process', methods=['POST'])
@token_required
def process_receipt_endpoint(current_user):
    """Process a receipt image and extract data"""

    if 'file' not in request.files:
        return jsonify({
            "error": "No file part in request"
        }), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({
            "error": "No file selected"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Invalid file type. Allowed: PNG, JPG, JPEG, WEBP, GIF, BMP"
        }), 400

    try:
        filename = werkzeug.utils.secure_filename(file.filename)

        # Add timestamp to make filename unique
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename

        upload_folder = current_app.config.get(
            'UPLOAD_FOLDER',
            'uploads'
        )

        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Process image
        processed_img_path = ImageProcessor.preprocess_image(file_path)

        # Extract text using OCR
        extracted_text = ocr_engine.extract_text(processed_img_path)

        if not extracted_text or len(extracted_text.strip()) < 10:
            return jsonify({
                "error": "Failed to extract text from receipt. Image quality may be too poor."
            }), 400

        # Parse structured data
        parsed_data = LLMParser.parse_receipt_text(extracted_text)

        # Predict expense category using the trained
        # TF-IDF + Logistic Regression model
        merchant = parsed_data.get('merchant', '')
        items = parsed_data.get('items', [])

        category = MLModel.predict(merchant, items)
        probabilities = MLModel.predict_proba(merchant, items)

        category_confidence = probabilities.get(category, 0.0)

        return jsonify({
            "message": "Receipt processed successfully",
            "image_filename": filename,
            "raw_ocr_text": extracted_text,
            "extracted_data": {
                'merchant': parsed_data.get('merchant') or 'Unknown Store',
                'merchant_name': parsed_data.get('merchant') or 'Unknown Store',
                'total': parsed_data.get('total') or 0.0,
                'total_amount': parsed_data.get('total') or 0.0,
                'receipt_date': parsed_data.get('date'),
                'date': parsed_data.get('date'),
                'category': category,
                'category_confidence': category_confidence,
                'category_probabilities': probabilities,
                'payment_method': parsed_data.get('payment_method') or 'Cash',
                'subtotal': parsed_data.get('subtotal'),
                'tax': parsed_data.get('tax'),
                'items': parsed_data.get('items', [])
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to process receipt: {str(e)}"
        }), 500


@receipts_bp.route('/save', methods=['POST'])
@token_required
def save_receipt_endpoint(current_user):
    """Save a processed receipt to database"""

    try:
        data = request.get_json() or {}

        # Validate required fields
        if 'total' not in data or data['total'] is None:
            return jsonify({
                "error": "Total amount is required"
            }), 400

        try:
            total = float(data.get('total'))

            if total < 0:
                return jsonify({
                    "error": "Total cannot be negative"
                }), 400

        except (ValueError, TypeError):
            return jsonify({
                "error": "Invalid total amount"
            }), 400

        # Parse date
        receipt_date = None

        if data.get('receipt_date'):
            try:
                receipt_date = datetime.strptime(
                    str(data['receipt_date']),
                    '%Y-%m-%d'
                ).date()
            except:
                pass

        # Create receipt
        new_receipt = Receipt(
            user_id=current_user.id,
            merchant_name=str(
                data.get('merchant_name', 'Unknown Store')
            ).strip() or 'Unknown Store',
            receipt_date=receipt_date,
            subtotal=float(data.get('subtotal') or 0.0),
            tax=float(data.get('tax') or 0.0),
            total=total,
            payment_method=str(
                data.get('payment_method', 'Other')
            ).strip() or 'Other',
            category=str(
                data.get('category', 'Other')
            ).strip() or 'Other',
            image_path=data.get('image_filename', ''),
            raw_ocr_text=data.get('raw_ocr_text', ''),
            status='COMPLETED'
        )

        db.session.add(new_receipt)
        db.session.flush()

        # Add line items
        for item in data.get('items', []):
            try:
                db.session.add(
                    ReceiptItem(
                        receipt_id=new_receipt.id,
                        item_name=str(
                            item.get('item_name', '')
                            or item.get('name', '')
                        ).strip() or 'Item',
                        quantity=float(
                            item.get('quantity') or 1.0
                        ),
                        price=float(
                            item.get('price') or 0.0
                        )
                    )
                )
            except:
                continue

        db.session.commit()

        return jsonify({
            'message': 'Receipt saved successfully',
            'receipt': new_receipt.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": f"Failed to save receipt: {str(e)}"
        }), 500


@receipts_bp.route('/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve uploaded receipt images"""

    try:
        upload_folder = current_app.config.get(
            'UPLOAD_FOLDER',
            'uploads'
        )

        # Security: only serve files that exist in the upload folder
        file_path = os.path.join(upload_folder, filename)

        # Verify the file is in the upload folder
        if not os.path.abspath(file_path).startswith(
            os.path.abspath(upload_folder)
        ):
            return jsonify({
                "error": "Invalid file path"
            }), 400

        if not os.path.exists(file_path):
            return jsonify({
                "error": "File not found"
            }), 404

        return send_from_directory(upload_folder, filename)

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            'error': f'Failed to process receipt: {str(e)}'
        }), 500