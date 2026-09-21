"""
Real Tesseract OCR wrapper for PARAKH.

Runs Tesseract on the original image and several OCR-friendly
preprocessing variants. All recognized text, confidence values,
and bounding boxes come directly from Tesseract.

No text is fabricated or guessed.
"""

import cv2
import pytesseract
from pytesseract import Output

from app.core.config import settings


if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


class OCRWordResult:
    __slots__ = (
        "text",
        "confidence",
        "x",
        "y",
        "width",
        "height",
        "line_num",
        "word_num",
    )

    def __init__(
        self,
        text,
        confidence,
        x,
        y,
        width,
        height,
        line_num,
        word_num,
    ):
        self.text = text
        self.confidence = confidence
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.line_num = line_num
        self.word_num = word_num


class OCRRunResult:
    def __init__(
        self,
        full_text: str,
        mean_confidence: float,
        words: list[OCRWordResult],
    ):
        self.full_text = full_text
        self.mean_confidence = mean_confidence
        self.words = words


def _run_tesseract(image, psm: int):
    """
    Run Tesseract on an OpenCV image and return raw OCR data.
    """

    data = pytesseract.image_to_data(
        image,
        lang="eng",
        config=f"--psm {psm}",
        output_type=Output.DICT,
    )

    words = []
    confidences = []
    lines = {}

    n = len(data.get("text", []))

    for i in range(n):
        raw_text = data["text"][i].strip()

        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1.0

        if not raw_text:
            continue

        block_num = int(data.get("block_num", [0] * n)[i])
        par_num = int(data.get("par_num", [0] * n)[i])
        line_num = int(data.get("line_num", [0] * n)[i])
        word_num = int(data.get("word_num", [0] * n)[i])

        line_key = (block_num, par_num, line_num)

        if line_key not in lines:
            lines[line_key] = []

        lines[line_key].append(raw_text)

        if conf >= 0:
            confidences.append(conf)

        words.append(
            OCRWordResult(
                text=raw_text,
                confidence=max(conf, 0.0),
                x=int(data["left"][i]),
                y=int(data["top"][i]),
                width=int(data["width"][i]),
                height=int(data["height"][i]),
                line_num=line_num,
                word_num=word_num,
            )
        )

    full_text = "\n".join(
        " ".join(line_words)
        for line_words in lines.values()
    )

    mean_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return full_text, mean_confidence, words


def _create_variants(image):
    """
    Create a small set of OCR-friendly image variants.

    The original image is intentionally kept because aggressive
    thresholding can destroy text on real product packaging.
    """

    variants = []

    # 1. Original
    variants.append(("original", image))

    # 2. Grayscale + CLAHE
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(gray)

    variants.append(("clahe", enhanced))

    # 3. Adaptive threshold
    adaptive = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    variants.append(("adaptive_threshold", adaptive))

    # 4. Otsu threshold
    _, otsu = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    variants.append(("otsu", otsu))

    return variants


def _score_result(text: str, confidence: float, words):
    """
    Choose the most useful OCR result.

    Confidence is important, but we also reward results containing
    common packaged-commodity declaration terms.
    """

    upper = text.upper()

    useful_terms = [
        "MRP",
        "NET",
        "WEIGHT",
        "QUANTITY",
        "PKD",
        "MFG",
        "MANUFACT",
        "USE BY",
        "BEST BEFORE",
        "LOT",
        "BATCH",
        "CONSUMER",
        "CARE",
        "IMPORT",
        "COUNTRY",
    ]

    term_hits = sum(
        1 for term in useful_terms
        if term in upper
    )

    word_count = len(words)

    # Confidence is the main factor.
    # Declaration-term hits help select a useful package-reading result.
    return (
        confidence * 1.0
        + term_hits * 4.0
        + min(word_count, 80) * 0.15
    )


def run_ocr(image_path: str, lang: str = "eng") -> OCRRunResult:
    """
    Runs multiple real Tesseract OCR passes on the image and returns
    the strongest result.

    The original image is included deliberately.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    variants = _create_variants(image)

    best_result = None
    best_score = float("-inf")
    best_name = None
    best_psm = None

    # Different PSM modes work better for different package layouts.
    psm_modes = [6, 11]

    for variant_name, variant_image in variants:
        for psm in psm_modes:
            try:
                text, confidence, words = _run_tesseract(
                    variant_image,
                    psm,
                )
            except Exception as e:
                print(
                    f"[PARAKH OCR ERROR] "
                    f"variant={variant_name}, PSM={psm}: {e}"
                )
                continue

            score = _score_result(
                text,
                confidence,
                words,
            )

            if score > best_score:
                best_score = score
                best_result = (text, confidence, words)
                best_name = variant_name
                best_psm = psm

    if best_result is None:
        return OCRRunResult(
            full_text="",
            mean_confidence=0.0,
            words=[],
        )

    full_text, mean_confidence, words = best_result

    print(
        f"[PARAKH OCR] Selected variant={best_name}, "
        f"PSM={best_psm}, "
        f"confidence={mean_confidence:.2f}, "
        f"words={len(words)}"
    )

    return OCRRunResult(
        full_text=full_text,
        mean_confidence=mean_confidence,
        words=words,
    )