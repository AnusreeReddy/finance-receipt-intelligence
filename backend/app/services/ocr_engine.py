import os
from paddleocr import PaddleOCR

class OCREngine:
    def __init__(self):
        self.reader = PaddleOCR(use_angle_cls=True, lang='en', enable_mkldnn=False)

    def extract_text(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Target OCR image does not exist: {image_path}")

        try:
            result = self.reader.ocr(image_path, cls=True)
        except Exception as exc:
            raise RuntimeError(f'PaddleOCR failed on {image_path}: {str(exc)}')

        extracted_lines = []

        for page in result:
            if not page:
                continue

            for line in page:
                if not line or len(line) < 2:
                    continue

                text_info = line[1]

                if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                    text = text_info[0]
                else:
                    text = text_info

                if isinstance(text, str) and text.strip():
                    extracted_lines.append(text.strip())

        return '\n'.join(extracted_lines)