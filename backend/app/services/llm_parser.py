import json
import re
import requests
from flask import current_app

class LLMParser:
    @staticmethod
    def _strip_wrapped_json(text):
        cleaned = str(text or '').strip()

        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s*```$', '', cleaned)

        return cleaned.strip()
    @staticmethod
    def _validate_payload(payload):
        if not isinstance(payload, dict):
            raise ValueError('LLM output must decode into a JSON object')

        normalized = {
            'merchant': payload.get('merchant') or payload.get('merchant_name') or 'Unknown Store',
            'total': float(payload.get('total') or payload.get('total_amount') or 0.0),
            'date': payload.get('date') or payload.get('receipt_date') or None,
            'items': payload.get('items') or [],
            'category': payload.get('category') or 'Other',
            'payment_method': payload.get('payment_method') or None,
            'subtotal': payload.get('subtotal'),
            'tax': payload.get('tax'),
        }
        if not isinstance(normalized['items'], list):
            normalized['items'] = []
        return normalized

    @staticmethod
    def parse_receipt_text(raw_ocr_text):
        """
        Sends extracted raw OCR text to Ollama Qwen2.5-VL to derive a structured JSON payload.
        """
        sanitized_ocr_text = re.sub(r'[%§sS](\d+\.\d{2})', r'$\1', raw_ocr_text or '')

        system_prompt = (
            'You are a specialized financial document parser. Return only strict JSON with the exact keys '
            'merchant, total, date, items. Do not wrap the response in markdown or code fences. '
            'If unknown, use null or an empty list.'
        )
        user_prompt = f"Receipt Raw OCR Text:\n{sanitized_ocr_text}"

        model_name = current_app.config.get('OLLAMA_MODEL', 'qwen2.5vl:7b')
        api_url = current_app.config.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')

        payload = {
            "model": model_name,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1
            }
        }

        try:
            response = requests.post(api_url, json=payload, timeout=120)
            response.raise_for_status()
            res_data = response.json()
            response_content = str(res_data.get('response', '{}'))
            cleaned_content = LLMParser._strip_wrapped_json(response_content)

            print("LLM RAW RESPONSE:")
            print(response_content)
            print("LLM CLEANED RESPONSE:")
            print(cleaned_content)

            parsed_json = json.loads(cleaned_content)
            return LLMParser._validate_payload(parsed_json)
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            current_app.logger.error(f"LLM Parsing failed: {str(e)}")
            total_match = re.search(r'(?:total|amount)\D*([\d.]+)', raw_ocr_text or '', re.IGNORECASE)
            extracted_total = float(total_match.group(1)) if total_match else 0.0

            return {
                "merchant": "Unknown Store",
                "receipt_date": None,
                "subtotal": None,
                "tax": None,
                "total": extracted_total,
                "payment_method": None,
                "category": "Other",
                "items": []
            }