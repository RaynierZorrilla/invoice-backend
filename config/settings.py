import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "ShipInvoice RD API"
    API_PREFIX = "/api"
    ENV = os.getenv("ENV", "dev")

settings = Settings()
