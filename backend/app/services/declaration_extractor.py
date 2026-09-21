"""
PARAKH declaration extractor.

Uses transparent pattern matching and OCR word positions.
It does not invent values.

Designed for real package OCR where:
- labels and values can be on different lines
- OCR may insert punctuation/noise
- dates may appear before or after their labels
- declaration labels may be partially missed
"""

import re
from dataclasses import dataclass

from app.services.ocr_service import OCRWordResult


# ---------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------

@dataclass
class ExtractedDeclaration:
    field: str
    detected_value: str | None
    normalized_value: str | None
    confidence: float | None
    ocr_confidence: float | None
    bbox: tuple[int, int, int, int] | None
    needs_verification: bool = False


# ---------------------------------------------------------------------
# Basic patterns
# ---------------------------------------------------------------------

DATE_RE = r"\d{1,2}\s*[/\-\.]\s*\d{1,2}\s*[/\-\.]\s*\d{2,4}"

NUMBER_RE = r"\d+(?:[.,]\d+)?"

UNIT_RE = r"(?:MG|G|GM|GRAMS?|KG|ML|L|LTR|LITRE|N)\b"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip(" :-–—.,;|()[]{}")


def _words_upper(words):
    return [(w, _normalize(w.text).upper()) for w in words]


def _bbox_for_words(
    selected: list[OCRWordResult],
):
    if not selected:
        return None, None

    x0 = min(w.x for w in selected)
    y0 = min(w.y for w in selected)
    x1 = max(w.x + w.width for w in selected)
    y1 = max(w.y + w.height for w in selected)

    confidence = sum(w.confidence for w in selected) / len(selected)

    return (
        (x0, y0, x1 - x0, y1 - y0),
        confidence,
    )


def _make_result(
    field: str,
    value: str,
    selected_words: list[OCRWordResult],
    verification: bool = False,
):
    value = _normalize(value)

    bbox, ocr_conf = _bbox_for_words(selected_words)

    if bbox:
        extraction_confidence = 0.80
    else:
        extraction_confidence = 0.55

    needs_verification = verification

    if bbox is None:
        needs_verification = True

    if ocr_conf is not None and ocr_conf < 60:
        needs_verification = True

    return ExtractedDeclaration(
        field=field,
        detected_value=value,
        normalized_value=value.upper(),
        confidence=extraction_confidence,
        ocr_confidence=ocr_conf,
        bbox=bbox,
        needs_verification=needs_verification,
    )


def _missing_result(field: str):
    return ExtractedDeclaration(
        field=field,
        detected_value=None,
        normalized_value=None,
        confidence=None,
        ocr_confidence=None,
        bbox=None,
        needs_verification=True,
    )


# ---------------------------------------------------------------------
# Find a value near a label
# ---------------------------------------------------------------------

def _find_number_near_label(
    words: list[OCRWordResult],
    label_patterns: list[str],
):
    """
    Finds a numeric value near a declaration label.

    This is more tolerant than requiring a perfect regex sentence.
    """

    if not words:
        return None

    indexed = _words_upper(words)

    for i, (word, text) in enumerate(indexed):

        if not any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in label_patterns
        ):
            continue

        nearby = indexed[
            max(0, i - 2):min(len(indexed), i + 10)
        ]

        for candidate_word, candidate_text in nearby:

            match = re.search(
                NUMBER_RE,
                candidate_text,
            )

            if match:
                value = match.group(0)

                selected = [word, candidate_word]

                return value, selected

    return None


def _find_date_near_label(
    words: list[OCRWordResult],
    label_patterns: list[str],
):
    """
    Finds a date near a declaration label.

    Supports:
        PKD
        14/07/26

    and:
        14/07/26
        USE BY

    When multiple dates are near a label, the closest date
    to the label is preferred.
    """

    if not words:
        return None

    indexed = _words_upper(words)

    # ------------------------------------------------------------
    # 1. Find the declaration label
    # ------------------------------------------------------------
    for i, (label_word, label_text) in enumerate(indexed):

        if not any(
            re.search(pattern, label_text, re.IGNORECASE)
            for pattern in label_patterns
        ):
            continue

        # --------------------------------------------------------
        # 2. Check dates immediately BEFORE the label.
        # --------------------------------------------------------
        before = indexed[max(0, i - 8):i]

        for candidate_word, candidate_text in reversed(before):

            match = re.search(
                DATE_RE,
                candidate_text,
            )

            if match:
                return (
                    match.group(0),
                    [candidate_word, label_word],
                )

        # --------------------------------------------------------
        # 3. Check dates AFTER the label.
        # --------------------------------------------------------
        after = indexed[
            i + 1:min(len(indexed), i + 8)
        ]

        for candidate_word, candidate_text in after:

            match = re.search(
                DATE_RE,
                candidate_text,
            )

            if match:
                return (
                    match.group(0),
                    [label_word, candidate_word],
                )

    return None


# ---------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------

def extract_declarations(
    full_text: str,
    words: list[OCRWordResult],
) -> list[ExtractedDeclaration]:

    results = []

    text = full_text.replace("\r\n", "\n").replace("\r", "\n")
    upper = text.upper()

    # ================================================================
    # NET QUANTITY
    # ================================================================

    net_value = None
    net_words = []

    # First try the normal pattern: number + unit.
    match = re.search(
        r"NET\s+(?:QTY|QUANTITY|WT|WEIGHT|CONTENT|CONTENTS)"
        r"\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*"
        r"(MG|G|GM|GRAMS?|KG|ML|L|LTR|LITRE|N)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        net_value = (
            f"{_normalize(match.group(1))} "
            f"{match.group(2).lower()}"
        )

        value_tokens = re.findall(
            r"[A-Z0-9.]+",
            match.group(0).upper(),
        )

        for w in words:
            if any(
                token in _normalize(w.text).upper()
                for token in value_tokens
            ):
                net_words.append(w)

    else:
        # OCR sometimes reads the "g" in "250g" as ")".
        malformed_match = re.search(
            r"NET\s+(?:QTY|QUANTITY|WT|WEIGHT|CONTENT|CONTENTS)"
            r"\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*\)",
            text,
            re.IGNORECASE,
        )

        if malformed_match:
            net_value = (
                f"{_normalize(malformed_match.group(1))} g"
            )

            value_tokens = [
                malformed_match.group(1).upper(),
            ]

            for w in words:
                if any(
                    token in _normalize(w.text).upper()
                    for token in value_tokens
                ):
                    net_words.append(w)

        else:
            found = _find_number_near_label(
                words,
                [
                    r"^NET$",
                    r"^WEIGHT$",
                    r"^QTY$",
                    r"^QUANTITY$",
                    r"^WT$",
                ],
            )

            if found:
                net_value, net_words = found

    if net_value:
        needs_verification = not bool(
            re.search(UNIT_RE, net_value.upper())
        )

        results.append(
            _make_result(
                "NET_QUANTITY",
                net_value,
                net_words,
                needs_verification,
            )
        )
    else:
        results.append(_missing_result("NET_QUANTITY"))

    # ================================================================
    # MRP
    # ================================================================

    mrp_value = None
    mrp_words = []

    match = re.search(
        rf"(?:M\s*\.?\s*R\s*\.?\s*P\s*\.?|"
        rf"MAXIMUM\s+RETAIL\s+PRICE)"
        rf".{{0,80}}?"
        rf"(?:₹|RS\.?|INR)?\s*({NUMBER_RE})",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if match:
        mrp_value = match.group(1)

        for w in words:
            if re.search(
                rf"\b{re.escape(mrp_value)}\b",
                w.text.replace(",", ""),
            ):
                mrp_words.append(w)
                break

    if not mrp_value:
        found = _find_number_near_label(
            words,
            [
                r"^MRP",
                r"^M\.?R\.?P",
                r"MAXIMUM",
                r"RETAIL",
            ],
        )

        if found:
            mrp_value, mrp_words = found

    if mrp_value:
        results.append(
            _make_result(
                "MRP",
                mrp_value,
                mrp_words,
            )
        )
    else:
        results.append(_missing_result("MRP"))

    # ================================================================
    # PACKING / MANUFACTURING / IMPORT DATE
    # ================================================================

    date_result = _find_date_near_label(
        words,
        [
            r"^PKD",
            r"^PACK",
            r"^PACKED",
            r"^MFG",
            r"^MFD",
            r"MANUFACT",
            r"IMPORTED",
            r"IMPORT",
        ],
    )

    if not date_result:
        dates = []

        for w in words:
            match = re.search(DATE_RE, w.text)

            if match:
                dates.append((match.group(0), [w]))

        if dates:
            date_result = dates[0]

    if date_result:
        date_value, date_words = date_result

        results.append(
            _make_result(
                "MFG_PACKING_IMPORT_DATE",
                date_value,
                date_words,
                verification=False,
            )
        )
    else:
        results.append(
            _missing_result(
                "MFG_PACKING_IMPORT_DATE"
            )
        )

    # ================================================================
    # BEST BEFORE / USE BY
    # ================================================================

    use_by_match = re.search(
        rf"\bUSE\s+BY\b[\s:.-]*({DATE_RE})",
        text,
        re.IGNORECASE,
    )

    if not use_by_match:
        use_by_match = re.search(
            rf"({DATE_RE})[\s:.-]*\bUSE\s+BY\b",
            text,
            re.IGNORECASE,
        )

    if use_by_match:
        use_by_value = _normalize(
            use_by_match.group(1)
        )

        use_by_words = [
            w
            for w in words
            if use_by_value.upper()
            in _normalize(w.text).upper()
        ]

        if not use_by_words:
            date_result = _find_date_near_label(
                words,
                [
                    r"^USE$",
                    r"^BY$",
                ],
            )

            if date_result:
                _, use_by_words = date_result

        results.append(
            _make_result(
                "BEST_BEFORE_USE_BY",
                use_by_value,
                use_by_words,
                verification=False,
            )
        )

    else:
        best_before_match = re.search(
            rf"\bBEST\s+BEFORE\b[\s:.-]*({DATE_RE})",
            text,
            re.IGNORECASE,
        )

        if not best_before_match:
            best_before_match = re.search(
                rf"({DATE_RE})[\s:.-]*\bBEST\s+BEFORE\b",
                text,
                re.IGNORECASE,
            )

        if best_before_match:
            best_before_value = _normalize(
                best_before_match.group(1)
            )

            best_before_words = [
                w
                for w in words
                if best_before_value.upper()
                in _normalize(w.text).upper()
            ]

            if not best_before_words:
                date_result = _find_date_near_label(
                    words,
                    [
                        r"^BEST$",
                        r"^BEFORE$",
                    ],
                )

                if date_result:
                    _, best_before_words = date_result

            results.append(
                _make_result(
                    "BEST_BEFORE_USE_BY",
                    best_before_value,
                    best_before_words,
                    verification=False,
                )
            )
        else:
            results.append(
                _missing_result(
                    "BEST_BEFORE_USE_BY"
                )
            )

    # ================================================================
    # MANUFACTURER / PACKER / IMPORTER
    # ================================================================

    manufacturer_match = re.search(
        r"(?:MANUFACTURED|PACKED|IMPORTED|MARKETED)"
        r"\s*(?:BY|FOR)?"
        r"\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z0-9,.&()'\/\-\s]{4,120})",
        text,
        re.IGNORECASE,
    )

    if manufacturer_match:
        value = _normalize(
            manufacturer_match.group(1)
        )

        bbox_words = []

        for w in words:
            if any(
                token in _normalize(w.text).upper()
                for token in re.findall(
                    r"[A-Za-z0-9]+",
                    value.upper(),
                )
            ):
                bbox_words.append(w)

        results.append(
            _make_result(
                "MANUFACTURER_PACKER_IMPORTER",
                value,
                bbox_words,
                verification=True,
            )
        )
    else:
        results.append(
            _missing_result(
                "MANUFACTURER_PACKER_IMPORTER"
            )
        )

    # ================================================================
    # COUNTRY OF ORIGIN
    # ================================================================

    country_match = re.search(
        r"(?:COUNTRY\s+OF\s+ORIGIN|MADE\s+IN)"
        r"\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z\s]{1,40})",
        text,
        re.IGNORECASE,
    )

    if country_match:
        value = _normalize(
            country_match.group(1)
        )

        results.append(
            _make_result(
                "COUNTRY_OF_ORIGIN",
                value,
                [],
                verification=True,
            )
        )
    else:
        results.append(
            _missing_result(
                "COUNTRY_OF_ORIGIN"
            )
        )

    # ================================================================
    # CONSUMER CARE
    # ================================================================

    consumer_match = re.search(
        r"(?:CONSUMER\s+CARE|CUSTOMER\s+CARE|"
        r"HELPLINE|TOLL\s*FREE)"
        r"\s*[:\-]?\s*"
        r"([A-Za-z0-9@.,+\-/()\s]{5,120})",
        text,
        re.IGNORECASE,
    )

    if consumer_match:
        value = _normalize(
            consumer_match.group(1)
        )

        results.append(
            _make_result(
                "CONSUMER_CARE",
                value,
                [],
                verification=True,
            )
        )
    else:
        results.append(
            _missing_result(
                "CONSUMER_CARE"
            )
        )

    # ================================================================
    # UNIT SALE PRICE
    # ================================================================

    unit_match = re.search(
        rf"UNIT\s+SALE\s+PRICE"
        rf"\s*[:\-]?\s*"
        rf"(?:₹|RS\.?|INR)?\s*"
        rf"({NUMBER_RE})",
        text,
        re.IGNORECASE,
    )

    if unit_match:
        results.append(
            _make_result(
                "UNIT_SALE_PRICE",
                unit_match.group(1),
                [],
                verification=True,
            )
        )
    else:
        results.append(
            _missing_result(
                "UNIT_SALE_PRICE"
            )
        )

    # ================================================================
    # DIMENSIONS
    # ================================================================

    dimension_match = re.search(
        r"(?:DIMENSIONS?|SIZE)"
        r"\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?"
        r"\s*[Xx]\s*"
        r"[0-9]+(?:\.[0-9]+)?"
        r"(?:\s*[Xx]\s*[0-9]+(?:\.[0-9]+)?)?"
        r"\s*(?:CM|MM|INCH(?:ES)?)?)",
        text,
        re.IGNORECASE,
    )

    if dimension_match:
        results.append(
            _make_result(
                "DIMENSIONS",
                dimension_match.group(1),
                [],
                verification=True,
            )
        )
    else:
        results.append(
            _missing_result(
                "DIMENSIONS"
            )
        )

    # ================================================================
    # PRODUCT NAME
    # ================================================================

    candidate = None

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    ignored = [
        "MRP",
        "NET WEIGHT",
        "NET QUANTITY",
        "USE BY",
        "BEST BEFORE",
        "LOT",
        "PKD",
        "MFG",
        "MFD",
        "CONSUMER CARE",
    ]

    for line in lines[:10]:

        clean_line = re.sub(
            r"^[^A-Za-z]+",
            "",
            line,
        ).strip()

        upper_line = clean_line.upper()

        if not clean_line:
            continue

        for phrase in [
            "NET WEIGHT",
            "NET QUANTITY",
            "NET QTY",
        ]:

            if phrase in upper_line:

                before = clean_line[
                    :upper_line.find(phrase)
                ].strip()

                if len(before) >= 3:
                    candidate = before
                    break

        if candidate:
            break

        if any(
            phrase in upper_line
            for phrase in ignored
        ):
            continue

        letters = sum(
            c.isalpha()
            for c in clean_line
        )

        if (
            letters >= 4
            and letters / max(len(clean_line), 1) > 0.55
        ):
            candidate = clean_line
            break

    if candidate:

        candidate_words = []

        for w in words:
            if any(
                token in _normalize(w.text).upper()
                for token in re.findall(
                    r"[A-Za-z]+",
                    candidate.upper(),
                )
            ):
                candidate_words.append(w)

        results.append(
            _make_result(
                "PRODUCT_NAME",
                candidate,
                candidate_words,
                verification=True,
            )
        )

    else:
        results.append(
            _missing_result(
                "PRODUCT_NAME"
            )
        )

    return results