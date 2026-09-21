"""Wrapper for backward compatibility with main pipeline module"""
from app.services.ml_model import MLModel

def predict_category(merchant, items=None):
    """Predict expense category"""
    return MLModel.predict(merchant, items)
