from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import func
from app.models import db, Receipt
from app.utils.auth_middleware import token_required
from app.services.anomaly_detector import AnomalyDetector
from app.services.ml_model import MLModel
import requests
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/summary', methods=['GET'])
@token_required
def get_analytics_summary(current_user):
    # Total Spending
    total_spent = db.session.query(func.sum(Receipt.total))\
        .filter(Receipt.user_id == current_user.id).scalar() or 0.0

    # Total Receipts Count
    total_receipts = Receipt.query.filter_by(user_id=current_user.id).count()

    # Category Breakdown
    category_stats = db.session.query(
        Receipt.category,
        func.sum(Receipt.total).label('cat_total'),
        func.count(Receipt.id).label('cat_count')
    ).filter(Receipt.user_id == current_user.id)\
     .group_by(Receipt.category).all()

    category_breakdown = [
        {
            'category': cat or 'Uncategorized',
            'total': float(total),
            'count': count
        }
        for cat, total, count in category_stats
    ]

    # Payment Method Breakdown
    payment_stats = db.session.query(
        Receipt.payment_method,
        func.sum(Receipt.total).label('pay_total')
    ).filter(Receipt.user_id == current_user.id)\
     .group_by(Receipt.payment_method).all()

    payment_breakdown = [
        {
            'payment_method': method or 'Other',
            'total': float(total)
        }
        for method, total in payment_stats
    ]

    return jsonify({
        'total_spent': float(total_spent),
        'total_receipts': total_receipts,
        'category_breakdown': category_breakdown,
        'payment_breakdown': payment_breakdown
    }), 200

@analytics_bp.route('/insights', methods=['GET'])
@token_required
def get_ai_insights(current_user):
    receipts = Receipt.query.filter_by(user_id=current_user.id).order_by(Receipt.receipt_date.desc()).all()

    if not receipts:
        return jsonify({
            'insights': "No expense data available. Upload your receipts to receive AI-powered spending analysis and budget optimization strategies."
        }), 200

    # Format expense summary for LLM analysis
    spending_summary = []
    for r in receipts[:25]:  # Analyze top 25 recent transactions
        spending_summary.append({
            'merchant': r.merchant_name,
            'date': r.receipt_date.isoformat() if r.receipt_date else 'Unknown',
            'category': r.category,
            'total': r.total
        })

    prompt = (
        "You are an expert personal financial advisor and AI budget analyst. "
        "Analyze the following recent user transactions and provide 3 concise, actionable, bulleted spending insights "
        "and recommendations to optimize their budget:\n\n"
        f"Transactions: {json.dumps(spending_summary)}\n\n"
        "Provide direct bullet points with key observations on category distribution and savings opportunities."
    )

    payload = {
        "model": current_app.config['OLLAMA_MODEL'],
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(
            current_app.config['OLLAMA_API_URL'],
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        res_data = response.json()
        insights_text = res_data.get('response', 'Unable to generate insights at this time.')
    except Exception as e:
        insights_text = "AI Analytics Service is currently offline. Ensure Ollama is running to get real-time spending insights."

    return jsonify({'insights': insights_text}), 200

@analytics_bp.route('/dashboard-data', methods=['GET'])
@token_required
def get_dashboard_data(current_user):
    category_stats = db.session.query(
        Receipt.category,
        func.sum(Receipt.total).label('cat_total'),
        func.count(Receipt.id).label('cat_count')
    ).filter(Receipt.user_id == current_user.id) \
     .group_by(Receipt.category).all()

    labels = []
    totals = []
    counts = []
    for category, total, count in category_stats:
        labels.append(category or 'Uncategorized')
        totals.append(float(total or 0.0))
        counts.append(int(count or 0))

    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Category Spend',
            'data': totals,
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8D6E63'
            ]
        }],
        'counts': counts
    }), 200


@analytics_bp.route('/anomalies', methods=['GET'])
@token_required
def get_anomalies(current_user):
    """Detect anomalous transactions in user's spending"""
    try:
        sensitivity = float(request.args.get('sensitivity', 0.8))
        sensitivity = min(1.0, max(0.0, sensitivity))  # Clamp to 0-1
        
        receipts = Receipt.query.filter_by(user_id=current_user.id).all()
        
        result = AnomalyDetector.detect_anomalies(receipts, sensitivity)
        summary = AnomalyDetector.get_anomaly_summary(result)
        
        return jsonify({
            'anomalies': result['anomalies'],
            'summary': summary,
            'total_detected': result['total_detected'],
            'high_severity': result['high_severity'],
            'medium_severity': result['medium_severity'],
            'low_severity': result['low_severity'],
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to detect anomalies: {str(e)}"}), 500


@analytics_bp.route('/model/evaluate', methods=['GET'])
@token_required
def evaluate_model(current_user):
    """Get model evaluation metrics"""
    try:
        # Get all user's transactions
        receipts = Receipt.query.filter_by(user_id=current_user.id).all()
        
        if len(receipts) < 10:
            return jsonify({
                'message': 'Need at least 10 transactions to evaluate model',
                'current_count': len(receipts)
            }), 400
        
        # Prepare descriptions and actual categories
        descriptions = []
        categories = []
        
        for r in receipts:
            merchant = r.merchant_name or 'Unknown'
            items = [item.item_name for item in r.items] if r.items else []
            descriptions.append(merchant + ' ' + ' '.join(items))
            categories.append(r.category)
        
        # Evaluate
        metrics = MLModel.evaluate(descriptions, categories)
        
        if metrics:
            return jsonify({
                'overall': {
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1'],
                },
                'by_category': metrics.get('by_category', {}),
                'samples_evaluated': len(receipts)
            }), 200
        else:
            return jsonify({
                'error': 'Model not found. Train the model first using the training script.'
            }), 404
    except Exception as e:
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500


@analytics_bp.route('/model/metrics', methods=['GET'])
@token_required
def get_model_metrics(current_user):
    """Get last computed model metrics"""
    metrics = MLModel.get_metrics()
    if metrics:
        return jsonify(metrics), 200
    return jsonify({'message': 'No metrics available yet. Run evaluation first.'}), 404


@analytics_bp.route('/trends', methods=['GET'])
@token_required
def get_spending_trends(current_user):
    """Get spending trends over time"""
    try:
        receipts = Receipt.query.filter_by(user_id=current_user.id)\
            .order_by(Receipt.receipt_date.desc()).all()
        
        if not receipts:
            return jsonify({'trends': {}}), 200
        
        # Group by month
        monthly_data = {}
        for r in receipts:
            if r.receipt_date:
                month_key = r.receipt_date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'total': 0, 'count': 0}
                monthly_data[month_key]['total'] += r.total
                monthly_data[month_key]['count'] += 1
        
        # Sort chronologically
        sorted_months = sorted(monthly_data.keys())
        
        return jsonify({
            'months': sorted_months,
            'totals': [monthly_data[m]['total'] for m in sorted_months],
            'counts': [monthly_data[m]['count'] for m in sorted_months],
            'monthly_data': {k: monthly_data[k] for k in sorted_months}
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get trends: {str(e)}"}), 500