import re
from datetime import datetime
from typing import Optional


def convert_to_standard_date(date_input: str) -> Optional[str]:
    """
    Convert various date formats to standard ISO date format (YYYY-MM-DD)

    Supports:
    - Persian dates: "۲۸ سپتامبر ۲۰۲۵", "8 سپتامبر 2025"
    - English dates: "September 28, 2025", "28/09/2025", "2025-09-28"
    - Mixed formats: "28 September 2025"
    """
    if not date_input or not date_input.strip():
        return None

    date_string = date_input.strip()

    # Try different parsing methods
    parsed_date = None

    # Method 1: Persian date parsing
    parsed_date = _parse_persian_date(date_string)
    if parsed_date:
        return parsed_date.strftime("%Y/%m/%d")

    # Method 2: English date parsing
    parsed_date = _parse_english_date(date_string)
    if parsed_date:
        return parsed_date.strftime("%Y/%m/%d")

    # Method 3: Numeric date parsing
    parsed_date = _parse_numeric_date(date_string)
    if parsed_date:
        return parsed_date.strftime("%Y/%m/%d")

    # If all methods fail, return original string
    return date_string


def _parse_persian_date(date_string: str) -> Optional[datetime]:
    """Parse Persian date formats"""
    try:
        # Persian month names mapping
        persian_months = {
            "ژانویه": 1,
            "فوریه": 2,
            "مارس": 3,
            "آوریل": 4,
            "مه": 5,
            "ژوئن": 6,
            "ژوئیه": 7,
            "اوت": 8,
            "سپتامبر": 9,
            "اکتبر": 10,
            "نوامبر": 11,
            "دسامبر": 12,
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        # Convert Persian digits to English
        persian_to_english = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        date_string = date_string.translate(persian_to_english)

        # Pattern: "28 September 2025" or "28 سپتامبر 2025"
        pattern = r"(\d{1,2})\s+(\w+)\s+(\d{4})"
        match = re.search(pattern, date_string, re.IGNORECASE)

        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))

            if month_name in persian_months:
                month = persian_months[month_name]
                return datetime(year, month, day)

        return None

    except Exception:
        return None


def _parse_english_date(date_string: str) -> Optional[datetime]:
    """Parse English date formats"""
    try:
        # Common English date formats
        formats = [
            "%B %d, %Y",  # September 28, 2025
            "%d %B %Y",  # 28 September 2025
            "%d/%m/%Y",  # 28/09/2025
            "%m/%d/%Y",  # 09/28/2025
            "%Y-%m-%d",  # 2025-09-28
            "%d-%m-%Y",  # 28-09-2025
            "%m-%d-%Y",  # 09-28-2025
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        return None

    except Exception:
        return None


def _parse_numeric_date(date_string: str) -> Optional[datetime]:
    """Parse numeric date formats"""
    try:
        # Remove any non-numeric characters except separators
        cleaned = re.sub(r"[^\d/.-]", "", date_string)

        # Try different numeric patterns
        patterns = [
            r"(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})",  # YYYY/MM/DD
            r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})",  # DD/MM/YYYY or MM/DD/YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                if len(match.group(1)) == 4:  # YYYY/MM/DD format
                    year, month, day = (
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                    )
                else:  # DD/MM/YYYY format (assuming DD/MM/YYYY)
                    day, month, year = (
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                    )

                # Validate date
                if 1 <= month <= 12 and 1 <= day <= 31 and year >= 1900:
                    return datetime(year, month, day)

        return None

    except Exception:
        return None


def validate_date_format(date_string: str) -> bool:
    """Validate if the date string can be converted to a valid date"""
    try:
        converted = convert_to_standard_date(date_string)
        if converted and converted != date_string:
            # Try to parse the converted date to ensure it's valid
            datetime.strptime(converted, "%Y/%m/%d")
            return True
        return False
    except Exception:
        return False
