import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from numvo import Numvo
from numvo.normalize import normalize_phone_number
from numvo.providers.ftc import FTCComplaintProvider
from numvo.providers.ipqs import IPQSPhoneReputationProvider
from numvo.providers.phonenumbers_provider import PhoneNumbersProvider

mcp = FastMCP("Numvo")

FTC_DB = Path("data/ftc_complaints.sqlite3")
providers = [
    PhoneNumbersProvider(),
    FTCComplaintProvider(FTC_DB),
]

ipqs_api_key = os.getenv("IPQS_API_KEY")
if ipqs_api_key:
    providers.append(IPQSPhoneReputationProvider(ipqs_api_key))

service = Numvo(providers)


@mcp.tool()
def check_phone_number(phone_number: str) -> dict:
    """Check a phone number using metadata plus independent reputation signals."""
    return service.check(phone_number).to_dict()


@mcp.tool()
def normalize_number(phone_number: str) -> str:
    """Normalize a phone number into E.164 format."""
    return normalize_phone_number(phone_number)


if __name__ == "__main__":
    mcp.run()
