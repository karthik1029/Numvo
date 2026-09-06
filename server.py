from pathlib import Path

from mcp.server.fastmcp import FastMCP

from numvo import Numvo
from numvo.normalize import normalize_phone_number
from numvo.providers.ftc import FTCComplaintProvider
from numvo.providers.phonenumbers_provider import PhoneNumbersProvider

mcp = FastMCP("Numvo")

FTC_DB = Path("data/ftc_complaints.sqlite3")
service = Numvo([
    PhoneNumbersProvider(),
    FTCComplaintProvider(FTC_DB),
])


@mcp.tool()
def check_phone_number(phone_number: str) -> dict:
    """Check a phone number and return metadata plus FTC complaint-based spam risk signals."""
    return service.check(phone_number).to_dict()


@mcp.tool()
def normalize_number(phone_number: str) -> str:
    """Normalize a phone number into E.164 format."""
    return normalize_phone_number(phone_number)


if __name__ == "__main__":
    mcp.run()
