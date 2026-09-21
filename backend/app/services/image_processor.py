import os
import cv2

class ImageProcessor:
    @staticmethod
    def preprocess_image(image_path):
        """
        Loads image, converts to grayscale, and enhances contrast for cleaner OCR output.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Target image for preprocessing does not exist: {image_path}")

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"OpenCV could not decode image: {image_path}")

        # Resize small images to improve OCR recognition rate
        height, width = img.shape
        if width < 1000:
            scale = 1000 / width
            img = cv2.resize(img, (1000, int(height * scale)), interpolation=cv2.INTER_CUBIC)

        # Apply adaptive contrast enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)

        # Save processed file next to the original
        dir_name, file_name = os.path.split(image_path)
        processed_path = os.path.join(dir_name, f"processed_{file_name}")
        cv2.imwrite(processed_path, enhanced)

        return processed_path