"""
Real OpenCV-based preprocessing. The original uploaded image is NEVER
modified or deleted - preprocessing always writes to a new file.
"""
import os
import cv2
import numpy as np


def _variance_of_laplacian(gray: np.ndarray) -> float:
    """Standard blur metric - higher is sharper."""
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def assess_quality(image_path: str) -> tuple[str, str]:
    """Returns (quality, reason). Quality in {GOOD, ACCEPTABLE, POOR}.

    This is a heuristic screen (blur + brightness + resolution), not a
    legal measurement tool. It exists purely to tell the field officer
    whether to recapture the photo - never to declare non-compliance.
    """
    img = cv2.imread(image_path)
    if img is None:
        return "POOR", "Image could not be read/decoded"

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = _variance_of_laplacian(gray)
    brightness = float(np.mean(gray))

    reasons = []
    quality = "GOOD"

    if min(h, w) < 500:
        quality = "POOR"
        reasons.append("resolution too low")
    elif min(h, w) < 900:
        quality = "ACCEPTABLE" if quality == "GOOD" else quality
        reasons.append("resolution is limited")

    if blur_score < 40:
        quality = "POOR"
        reasons.append("image appears blurry")
    elif blur_score < 100 and quality != "POOR":
        quality = "ACCEPTABLE"
        reasons.append("image sharpness is marginal")

    if brightness < 40:
        quality = "POOR"
        reasons.append("image is too dark")
    elif brightness > 235:
        quality = "POOR"
        reasons.append("image is overexposed")

    reason_text = "; ".join(reasons) if reasons else "Image quality is adequate for OCR"
    return quality, reason_text


def preprocess_image(original_path: str, output_dir: str) -> str:
    """Runs a real OpenCV preprocessing pipeline (resize, grayscale, denoise,
    adaptive threshold) and writes the result to a NEW file. The original
    file at original_path is left untouched.
    """
    img = cv2.imread(original_path)
    if img is None:
        raise ValueError(f"Could not decode image at {original_path}")

    # 1. Resize - upscale small images so Tesseract has enough resolution
    h, w = img.shape[:2]
    target_min_dim = 1200
    scale = target_min_dim / min(h, w) if min(h, w) < target_min_dim else 1.0
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 4. Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 5. Adaptive threshold - helps Tesseract on uneven package lighting
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(original_path))[0]
    out_path = os.path.join(output_dir, f"{base_name}_preprocessed.png")
    cv2.imwrite(out_path, thresh)
    return out_path


def get_image_dimensions(path: str) -> tuple[int, int]:
    img = cv2.imread(path)
    if img is None:
        return 0, 0
    h, w = img.shape[:2]
    return w, h
