from api.services.date_converter import convert_to_standard_date, validate_date_format


def test_date_conversion():
    """Test various date formats"""

    test_cases = [
        # Persian dates
        "۲۸ سپتامبر ۲۰۲۵",
        "8 سپتامبر 2025",
        "۱۵ ژانویه ۲۰۲۶",
        # English dates
        "September 28, 2025",
        "28 September 2025",
        "28/09/2025",
        "09/28/2025",
        "2025-09-28",
        "28-09-2025",
        # Mixed formats
        "28 September 2025",
        "Sep 28, 2025",
        # Edge cases
        "2025/09/28",
        "28.09.2025",
    ]

    print("🧪 Testing Date Conversion")
    print("=" * 50)

    for test_date in test_cases:
        try:
            converted = convert_to_standard_date(test_date)
            is_valid = validate_date_format(test_date)

            status = "✅" if is_valid else "❌"
            print(f"{status} '{test_date}' → '{converted}'")

        except Exception as e:
            print(f"❌ '{test_date}' → Error: {e}")

    print("\n" + "=" * 50)
    print("✅ Date conversion test completed!")


if __name__ == "__main__":
    test_date_conversion()
