import os
from dotenv import load_dotenv

SETTINGS_FILE="settings.env"
# Load environment variables from file
load_dotenv("settings.env")

def get_env(key: str, optional = False):
    """
    Get an environment variable if it exists. Otherwise, fail with a helpful message.
    """
    value = os.getenv(key)
    if not optional and value is None:
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
TZKT_ENDPOINT = get_env('TZKT_ENDPOINT')

COLLATERAL_TOKEN = get_env('COLLATERAL_TOKEN')
SYNTHETIC_ASSET_TOKEN = get_env('SYNTHETIC_ASSET_TOKEN')
MINIMUM_PAYOUT = int(get_env('MINIMUM_PAYOUT'))
STEP_IN_RATIO = float(get_env('STEP_IN_RATIO'))

# Log
LOG_LEVEL = get_env('LOG_LEVEL', True)
LOG_LEVEL = 20 if LOG_LEVEL is None else int(LOG_LEVEL)
