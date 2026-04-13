import pdfplumber
import re
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ExtractedDates:
    start_date: date | None = None
    end_date: date | None = None
    signing_date: date | None = None
    all_dates: list[date] = None

    def __post_init__(self):
        if self.all_dates is None:
            self.all_dates = []


DATE_PATTERNS = [
    (r"(\d{1,2})\s*de\s*(janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s*de\s*(\d{4})", "br_extenso"),
    (r"(\d{1,2})/(\d{1,2})/(\d{4})", "br_numeric"),
    (r"(\d{1,2})-(\d{1,2})-(\d{4})", "br_dash"),
    (r"(\d{4})-(\d{1,2})-(\d{1,2})", "iso"),
]

MONTH_MAP = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12
}

CONTEXT_PATTERNS = {
    "start": [
        r"(?:data\s+de\s+)?in[ií]cio[:\s]+",
        r"vigência\s+(?:a\s+partir|de)[:\s]+",
        r"come[çc]a(?:ndo)?\s+(?:em|a\s+partir\s+de)[:\s]+",
        r"a\s+partir\s+de[:\s]+",
    ],
    "end": [
        r"(?:data\s+de\s+)?(?:t[ée]rmino|vencimento|fim)[:\s]+",
        r"vigência\s+até[:\s]+",
        r"válido\s+até[:\s]+",
        r"expira(?:ção)?\s+em[:\s]+",
        r"encerra(?:mento)?\s+em[:\s]+",
        r"prazo\s+final[:\s]+",
    ],
    "signing": [
        r"(?:data\s+de\s+)?assinatura[:\s]+",
        r"firmado\s+em[:\s]+",
        r"assinado\s+em[:\s]+",
        r"celebrado\s+em[:\s]+",
    ]
}


def parse_date(match: tuple, pattern_type: str) -> date | None:
    try:
        if pattern_type == "br_extenso":
            day, month_name, year = match
            month = MONTH_MAP.get(month_name.lower())
            if month:
                return date(int(year), month, int(day))
        elif pattern_type in ("br_numeric", "br_dash"):
            day, month, year = match
            return date(int(year), int(month), int(day))
        elif pattern_type == "iso":
            year, month, day = match
            return date(int(year), int(month), int(day))
    except (ValueError, TypeError):
        pass
    return None


def extract_all_dates(text: str) -> list[date]:
    dates = []
    for pattern, pattern_type in DATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            parsed = parse_date(match.groups(), pattern_type)
            if parsed and 1990 <= parsed.year <= 2100:
                dates.append(parsed)
    return sorted(set(dates))


def find_contextual_date(text: str, context_type: str) -> date | None:
    patterns = CONTEXT_PATTERNS.get(context_type, [])
    for context_pattern in patterns:
        for date_pattern, pattern_type in DATE_PATTERNS:
            full_pattern = context_pattern + r"\s*" + date_pattern
            match = re.search(full_pattern, text, re.IGNORECASE)
            if match:
                date_groups = match.groups()[-3:]
                parsed = parse_date(date_groups, pattern_type)
                if parsed:
                    return parsed
    return None


def extract_dates_from_pdf(pdf_path: str | Path) -> ExtractedDates:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

    full_text_lower = full_text.lower()

    result = ExtractedDates()
    result.all_dates = extract_all_dates(full_text)

    result.start_date = find_contextual_date(full_text_lower, "start")
    result.end_date = find_contextual_date(full_text_lower, "end")
    result.signing_date = find_contextual_date(full_text_lower, "signing")

    if result.all_dates and len(result.all_dates) >= 2:
        if not result.start_date:
            result.start_date = result.all_dates[0]
        if not result.end_date:
            result.end_date = result.all_dates[-1]

    return result


def extract_contract_value(pdf_path: str | Path) -> float | None:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return None

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

    value_patterns = [
        r"(?:valor\s+(?:total|global|do\s+contrato))[:\s]+R\$\s*([\d.,]+)",
        r"R\$\s*([\d.,]+)(?:\s*\([^)]+\))?(?:\s*(?:mensais|anuais|por\s+m[êe]s))?",
    ]

    for pattern in value_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value_str = match.group(1)
            value_str = value_str.replace(".", "").replace(",", ".")
            try:
                return float(value_str)
            except ValueError:
                continue

    return None
