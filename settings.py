import os
from dotenv import load_dotenv

SETTINGS_FILE="settings.env"
# Load environment variables from file
load_dotenv("settings.env")

def get_env(key: str):
    """
    Get an environment variable if it exists. Otherwise, fail with a helpful message.
    """
    value = os.getenv(key)
    if value is None:
        print(f"""
        Configuration key '{key}' is missing.

        Make sure you include it in '{SETTINGS_FILE}' file or that you pass it when calling the script:

            Example: {key}=... python liquidation_bot.py
        """)
        exit()
    return value

# Secrets
PRIVATE_KEY = get_env('PRIVATE_KEY')
# API's
RPC_ENDPOINT = get_env('RPC_ENDPOINT')
INDEXER_ENDPOINT = get_env('INDEXER_ENDPOINT')
TZKT_ENDPOINT = get_env('TZKT_ENDPOINT')
# Contract addresses
ENGINE_ADDRESS = get_env('ENGINE_ADDRESS')
TARGET_PRICE_ORACLE_ADDRESS = get_env('TARGET_PRICE_ORACLE_ADDRESS')
TOKEN_ADDRESS = get_env('TOKEN_ADDRESS')
# Other
EMERGENCY_RATIO = float(get_env('EMERGENCY_RATIO'))
