"""
ML Model Service for expense categorization.
Provides training, inference, and evaluation capabilities.
"""

import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score
from nltk.stem import WordNetLemmatizer
import nltk

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()


class MLModel:
    """Expense categorization model with consistent preprocessing"""
    
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'category_model.pkl')
    VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'vectorizer.pkl')
    
    # Standard categories
    VALID_CATEGORIES = {
        'Food', 'Travel', 'Entertainment', 'Shopping', 'Health',
        'Utilities', 'Education', 'Housing', 'Insurance', 'Other'
    }
    
    _model = None
    _vectorizer = None
    _metrics = None
    
    @staticmethod
    def preprocess_text(text):
        """Consistent text preprocessing"""
        text = str(text or '').strip().lower()
        # Simple tokenization and lemmatization
        tokens = text.split()
        lemmatized = [lemmatizer.lemmatize(word) for word in tokens if len(word) > 2]
        return ' '.join(lemmatized)
    
    @classmethod
    def load_model(cls):
        """Load trained model and vectorizer"""
        if cls._model is not None:
            return cls._model, cls._vectorizer
        
        os.makedirs(os.path.dirname(cls.MODEL_PATH), exist_ok=True)
        
        if os.path.exists(cls.MODEL_PATH) and os.path.exists(cls.VECTORIZER_PATH):
            try:
                cls._model = joblib.load(cls.MODEL_PATH)
                cls._vectorizer = joblib.load(cls.VECTORIZER_PATH)
                return cls._model, cls._vectorizer
            except Exception:
                pass
        
        return None, None
    
    @classmethod
    def train(cls, descriptions, categories):
        """Train model on expense descriptions"""
        os.makedirs(os.path.dirname(cls.MODEL_PATH), exist_ok=True)
        
        # Preprocess
        processed_texts = [cls.preprocess_text(desc) for desc in descriptions]
        
        # Vectorize
        cls._vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        X = cls._vectorizer.fit_transform(processed_texts)
        
        # Train
        cls._model = LogisticRegression(max_iter=200, random_state=42)
        cls._model.fit(X, categories)
        
        # Save
        joblib.dump(cls._model, cls.MODEL_PATH)
        joblib.dump(cls._vectorizer, cls.VECTORIZER_PATH)
        
        return cls._model, cls._vectorizer
    
    @classmethod
    def predict(cls, merchant, items=None):
        """Predict category for a transaction"""
        model, vectorizer = cls.load_model()
        
        if model is None or vectorizer is None:
            return 'Other'
        
        # Prepare text
        item_text = ' '.join(str(item).strip() for item in (items or []) if str(item).strip())
        combined_text = f"{merchant or ''} {item_text}".strip()
        
        if not combined_text:
            return 'Other'
        
        try:
            processed = cls.preprocess_text(combined_text)
            X = vectorizer.transform([processed])
            prediction = model.predict(X)[0]
            return prediction if prediction in cls.VALID_CATEGORIES else 'Other'
        except Exception:
            return 'Other'
    
    @classmethod
    def predict_proba(cls, merchant, items=None):
        """Get prediction probabilities"""
        model, vectorizer = cls.load_model()
        
        if model is None or vectorizer is None:
            return {}
        
        item_text = ' '.join(str(item).strip() for item in (items or []) if str(item).strip())
        combined_text = f"{merchant or ''} {item_text}".strip()
        
        if not combined_text:
            return {}
        
        try:
            processed = cls.preprocess_text(combined_text)
            X = vectorizer.transform([processed])
            probas = model.predict_proba(X)[0]
            result = {cat: float(prob) for cat, prob in zip(model.classes_, probas)}
            return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
        except Exception:
            return {}
    
    @classmethod
    def evaluate(cls, descriptions, categories):
        """Evaluate model and return metrics"""
        model, vectorizer = cls.load_model()
        
        if model is None or vectorizer is None:
            return None
        
        try:
            processed_texts = [cls.preprocess_text(desc) for desc in descriptions]
            X = vectorizer.transform(processed_texts)
            predictions = model.predict(X)
            
            metrics = {
                'precision': float(precision_score(categories, predictions, average='weighted', zero_division=0)),
                'recall': float(recall_score(categories, predictions, average='weighted', zero_division=0)),
                'f1': float(f1_score(categories, predictions, average='weighted', zero_division=0)),
            }
            
            # Per-category metrics
            category_metrics = {}
            for cat in model.classes_:
                cat_mask = [c == cat for c in categories]
                cat_preds = [p == cat for p in predictions]
                
                if any(cat_mask):
                    cat_precision = precision_score([int(m) for m in cat_mask], [int(p) for p in cat_preds], zero_division=0)
                    cat_recall = recall_score([int(m) for m in cat_mask], [int(p) for p in cat_preds], zero_division=0)
                    cat_f1 = f1_score([int(m) for m in cat_mask], [int(p) for p in cat_preds], zero_division=0)
                    
                    category_metrics[cat] = {
                        'precision': float(cat_precision),
                        'recall': float(cat_recall),
                        'f1': float(cat_f1),
                        'support': sum(cat_mask)
                    }
            
            metrics['by_category'] = category_metrics
            cls._metrics = metrics
            return metrics
        except Exception as e:
            return None
    
    @classmethod
    def get_metrics(cls):
        """Get last computed metrics"""
        return cls._metrics
