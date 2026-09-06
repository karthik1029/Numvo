import phonenumbers


def normalize_phone_number(phone_number: str, default_region: str = "US") -> str:
    parsed = phonenumbers.parse(phone_number, default_region)
    if not phonenumbers.is_possible_number(parsed):
        raise ValueError("Invalid phone number")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
