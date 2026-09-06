from numvo.providers.phonenumbers_provider import PhoneNumbersProvider


def test_phonenumbers_provider_returns_metadata():
    provider = PhoneNumbersProvider()

    result = provider.lookup("+12025550123")

    assert result.provider == "phonenumbers"
    assert result.category == "phone_metadata"
    assert result.metadata["country_code"] == 1
    assert result.metadata["national_number"] == 2025550123
    assert "valid" in result.metadata
    assert "possible" in result.metadata
    assert "number_type" in result.metadata
