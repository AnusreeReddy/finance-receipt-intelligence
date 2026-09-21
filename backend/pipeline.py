import json
import os
import re
from typing import Any, Dict, List

import cv2
import joblib
import numpy as np
import requests

try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CANDIDATES = [
    os.path.join(BASE_DIR, 'receipt_category_model.pkl'),
    os.path.join(BASE_DIR, 'models', 'receipt_category_model.pkl'),
    os.path.join(BASE_DIR, 'app', 'models', 'receipt_category_model.pkl'),
    os.path.join(BASE_DIR, 'expense_categorization_model.pkl'),
]

OCR_MODEL = None
if PaddleOCR is not None:
    try:
        OCR_MODEL = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    except Exception:
        OCR_MODEL = None

SBERT_MODEL = None
if SentenceTransformer is not None:
    try:
        SBERT_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        SBERT_MODEL = None

LR_MODEL = None
for candidate in MODEL_CANDIDATES:
    if os.path.exists(candidate):
        try:
            LR_MODEL = joblib.load(candidate)
            break
        except Exception:
            continue


def preprocess_receipt_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Target image for preprocessing does not exist: {image_path}")

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"OpenCV could not decode image: {image_path}")

    height, width = img.shape
    if width < 1000:
        scale = 1000 / width
        img = cv2.resize(img, (1000, int(height * scale)), interpolation=cv2.INTER_CUBIC)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)

    dir_name, file_name = os.path.split(image_path)
    processed_path = os.path.join(dir_name, f"processed_{file_name}")
    cv2.imwrite(processed_path, enhanced)
    return processed_path


def extract_text_from_image(image_path: str) -> str:
    if OCR_MODEL is None:
        raise RuntimeError('PaddleOCR model could not be initialized')
    try:
        result = OCR_MODEL.ocr(image_path, cls=True)
        lines = []
        for page in result:
            for line in page:
                text = line[1]
                if isinstance(text, str) and text.strip():
                    lines.append(text)
        return '\n'.join(lines)
    except Exception as exc:
        raise RuntimeError(f'OCR extraction failed: {str(exc)}')


def _strip_wrapping_markdown(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^[\s\S]*?\{', '{', cleaned)
    cleaned = re.sub(r'\}[\s\S]*?$', '}', cleaned)
    return cleaned.strip()


def _safe_json_loads(raw_text: str) -> Dict[str, Any]:
    cleaned = _strip_wrapping_markdown(raw_text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
        if not match:
            raise
        payload = json.loads(match.group(0))

    if not isinstance(payload, dict):
        raise ValueError('LLM output must be a JSON object')
    return payload


def extract_receipt_json(raw_ocr_text: str) -> Dict[str, Any]:
    sanitized_ocr_text = re.sub(r'[%§sS](\d+\.\d{2})', r'$\1', raw_ocr_text or '')
    system_prompt = (
        'You are a specialized financial receipt parser. Return only strict JSON with keys '
        'merchant, total, date, items. Do not wrap the answer in markdown or code fences. '
        'If a value is unknown, use null or an empty list as appropriate.'
    )
    user_prompt = (
        'Extract receipt information from the OCR text and return strict JSON only.\n'
        f'Raw OCR Text:\n{sanitized_ocr_text}'
    )

    payload = {
        'model': 'qwen2.5-vl',
        'prompt': f"{system_prompt}\n\n{user_prompt}",
        'stream': False,
        'format': 'json',
        'options': {'temperature': 0.1},
    }

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        res_data = response.json()
        content = str(res_data.get('response', '{}'))
        parsed = _safe_json_loads(content)

        merchant = parsed.get('merchant') or parsed.get('merchant_name') or 'Unknown Store'
        total = parsed.get('total') or parsed.get('total_amount') or 0.0
        date = parsed.get('date') or parsed.get('receipt_date') or None
        items = parsed.get('items') or []

        if not isinstance(items, list):
            items = []

        return {
            'merchant': str(merchant),
            'total': float(total),
            'date': str(date) if date is not None else None,
            'items': items,
        }
    except Exception:
        total_match = re.search(r'(?:total|amount)\D*([\d.]+)', sanitized_ocr_text, re.IGNORECASE)
        extracted_total = float(total_match.group(1)) if total_match else 0.0
        return {
            'merchant': 'Unknown Store',
            'total': extracted_total,
            'date': None,
            'items': [],
        }


def predict_category(merchant: str, items: List[Any]) -> str:
    if SBERT_MODEL is None or LR_MODEL is None:
        return 'Other'

    item_text = ' '.join(str(item).strip() for item in items if str(item).strip())
    combined = f"{merchant or ''} {item_text}".strip()
    if not combined:
        return 'Other'

    embedding = SBERT_MODEL.encode([combined], normalize_embeddings=True)
    embedding = np.asarray(embedding, dtype=np.float32)
    if embedding.ndim > 2:
        embedding = embedding.reshape(1, -1)

    try:
        predicted_label = LR_MODEL.predict(embedding)[0]
        return str(predicted_label)
    except Exception:
        return 'Other'


def process_receipt(image_path: str) -> Dict[str, Any]:
    try:
        processed_path = preprocess_receipt_image(image_path)
        raw_text = extract_text_from_image(processed_path)
        parsed = extract_receipt_json(raw_text)
        category = predict_category(parsed.get('merchant', ''), parsed.get('items', []))
        return {
            'success': True,
            'merchant': parsed.get('merchant', 'Unknown Store'),
            'total': float(parsed.get('total') or 0.0),
            'date': parsed.get('date'),
            'items': parsed.get('items', []),
            'category': category,
            'description': parsed.get('merchant', 'Unknown Store'),
            'raw_ocr_text': raw_text,
        }
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc),
        }
