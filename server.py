from mcp.server.fastmcp import FastMCP

from numvo import Numvo
from numvo.normalize import normalize_phone_number
from numvo.providers.mock import MockReputationProvider
from numvo.providers.phonenumbers_provider import PhoneNumbersProvider

mcp = FastMCP("Numvo")
service = Numvo([
    PhoneNumbersProvider(),
    MockReputationProvider(),
])


@mcp.tool()
def check_phone_number(phone_number: str) -> dict:
    """Check a phone number and return its normalized form, spam score, risk, and provider signals."""
    return service.check(phone_number).to_dict()


@mcp.tool()
def normalize_number(phone_number: str) -> str:
    """Normalize a phone number into E.164 format."""
    return normalize_phone_number(phone_number)


if __name__ == "__main__":
    mcp.run()
