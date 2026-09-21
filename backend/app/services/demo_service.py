"""
DEMO MODE: provides sample cases when a live camera/upload isn't available
(e.g. presentation/testing). Demo inspections are clearly flagged
is_demo=True and use real package-label images generated as text renders
so the REAL OCR/compliance pipeline still runs on them - nothing about the
downstream analysis is faked, only the input images are synthetic
placeholders standing in for a physically scanned package.
"""
import os
from PIL import Image, ImageDraw, ImageFont

DEMO_DIR = "uploads/demo_samples"

SAMPLE_LABELS = {
    "mostly_compliant": [
        "FRESHTASTE COOKIES",
        "Net Wt. 200 G",
        "MRP Rs. 45.00 (Incl. of all taxes)",
        "Mfg Date: 05/2026",
        "Best Before 6 Months From Packaging",
        "Manufactured by: Freshtaste Foods Pvt Ltd, Nashik, Maharashtra",
        "Consumer Care: care@freshtaste.example, 1800-123-4567",
    ],
    "missing_declaration": [
        "SPARKLE DISH WASH LIQUID",
        "Net Qty 500 ML",
        "Mfg By: Sparkle Home Products Ltd",
        # MRP intentionally omitted
    ],
    "format_issue": [
        "TROPICANA STYLE JUICE",
        "Net Contents 1 L",
        "MRP ..... please see pack",  # malformed MRP on purpose
        "Packed on: 2026",  # incomplete date on purpose
        "Marketed by: Tropi Beverages Pvt Ltd",
    ],
    "poor_quality": [
        "??? ??  #### product",
    ],
}


def _render_label_image(lines: list[str], path: str, blurry: bool = False):
    width, height = 900, 700
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=28)
    except TypeError:
        font = ImageFont.load_default()

    y = 40
    for line in lines:
        draw.text((40, y), line, fill=(10, 10, 10), font=font)
        y += 60

    if blurry:
        # Simulate a poor-quality capture: heavy blur + low contrast
        from PIL import ImageFilter
        img = img.filter(ImageFilter.GaussianBlur(radius=6))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def generate_demo_case(case_key: str) -> str:
    """Generates (or reuses) a synthetic package-label image for the given
    demo case and returns its file path. Real OCR/extraction/rules still run
    on this image - only the "package photo" itself is a stand-in."""
    if case_key not in SAMPLE_LABELS:
        raise ValueError(f"Unknown demo case: {case_key}")

    path = os.path.join(DEMO_DIR, f"{case_key}.png")
    if not os.path.exists(path):
        _render_label_image(SAMPLE_LABELS[case_key], path, blurry=(case_key == "poor_quality"))
    return path


DEMO_CASES = {
    "mostly_compliant": {
        "label": "Mostly compliant product",
        "product_name": "Freshtaste Cookies",
        "brand": "Freshtaste",
        "category": "Food - Snacks",
    },
    "missing_declaration": {
        "label": "Missing declaration (MRP)",
        "product_name": "Sparkle Dish Wash Liquid",
        "brand": "Sparkle",
        "category": "Household",
    },
    "format_issue": {
        "label": "Potential declaration-format issue",
        "product_name": "Tropicana Style Juice",
        "brand": "Tropi Beverages",
        "category": "Food - Beverage",
    },
    "poor_quality": {
        "label": "Poor-quality image",
        "product_name": "Unidentified Product",
        "brand": "Unknown",
        "category": "General",
    },
}
