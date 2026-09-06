from phonenumbers import PhoneNumberType, carrier, geocoder, number_type, parse
from phonenumbers import is_possible_number, is_valid_number

from numvo.models import ProviderResult
from numvo.providers.base import PhoneIntelligenceProvider


_TYPE_NAMES = {
    PhoneNumberType.FIXED_LINE: "fixed_line",
    PhoneNumberType.MOBILE: "mobile",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
    PhoneNumberType.TOLL_FREE: "toll_free",
    PhoneNumberType.PREMIUM_RATE: "premium_rate",
    PhoneNumberType.SHARED_COST: "shared_cost",
    PhoneNumberType.VOIP: "voip",
    PhoneNumberType.PERSONAL_NUMBER: "personal_number",
    PhoneNumberType.PAGER: "pager",
    PhoneNumberType.UAN: "uan",
    PhoneNumberType.VOICEMAIL: "voicemail",
    PhoneNumberType.UNKNOWN: "unknown",
}


class PhoneNumbersProvider(PhoneIntelligenceProvider):
    """Local phone-number metadata provider backed by the phonenumbers package."""

    name = "phonenumbers"

    def lookup(self, phone_number: str) -> ProviderResult:
        parsed = parse(phone_number, None)

        metadata = {
            "valid": is_valid_number(parsed),
            "possible": is_possible_number(parsed),
            "region": geocoder.description_for_number(parsed, "en") or None,
            "carrier": carrier.name_for_number(parsed, "en") or None,
            "number_type": _TYPE_NAMES.get(number_type(parsed), "unknown"),
            "country_code": parsed.country_code,
            "national_number": parsed.national_number,
        }

        return ProviderResult(
            provider=self.name,
            confidence=1.0,
            category="phone_metadata",
            metadata=metadata,
        )
