from dotenv import load_dotenv
import os

from client.client import GoLoginClient

load_dotenv()
print("TOKEN EXISTS:", bool(os.getenv("GOLOGIN_TOKEN")))
print("TOKEN LENGTH:", len(os.getenv("GOLOGIN_TOKEN", "")))
print("PROFILE:", os.getenv("GOLOGIN_PROFILE_ID"))

URL = "https://prague.pasport.org.ua/solutions/e-queue"

data = {
    "form": "days",
    "ServiceCenter": "8",
    "ServiceId": "1",
    "8ad86be4d6d981cdc4641cd2fc1ff98": "1",
}

client = GoLoginClient()

client.open()

days = client.check_days()

print("Available days:", days)
