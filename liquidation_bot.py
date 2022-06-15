import time
import requests
import os
from dotenv import load_dotenv
from pytezos import pytezos
import traceback

# Load environment variables
load_dotenv("settings.env")
SHELL = os.getenv('RPC_ENDPOINT', 'https://mainnet.api.tez.ie')
KEY = os.getenv('PRIVATE_KEY')

pytezos_cli = pytezos.using(shell=SHELL, key=KEY)

INDEXER_URL = "https://youves-mainnet-indexer.dev.gke.papers.tech/v1/graphql/"
VAULT_COLLATERALIZATION_QUERY = """
query get_vaults($ratio: float8, $engine_contract_address:String) {
  vault(
      order_by: { ratio: asc }
      where: {
        ratio: { _lte: $ratio },
        engine_contract_address: { _eq: $engine_contract_address }
      }) {
      balance
      minted
      ratio
      address
      owner
  }
}
"""
ENGINE_ADDRESS = "KT1FFE2LC5JpVakVjHm5mM36QVp2p3ZzH4hH"
TARGET_PRICE_ORACLE_ADDRESS = "KT1P8Ep9y8EsDSD9YkvakWnDvF2orDcpYXSq"
TOKEN_ADDRESS = "KT1XRPEPXbZK25r3Htzp2o1x7xdMMmfocKNW"

EMERGENCY_RATIO = 2.0

last_now = pytezos_cli.now()

engine = pytezos_cli.contract(ENGINE_ADDRESS)
oracle = pytezos_cli.contract(TARGET_PRICE_ORACLE_ADDRESS)
token = pytezos_cli.contract(TOKEN_ADDRESS)

def log(message):
    print(f"[{int(time.time())}:{pytezos_cli.key.public_key_hash()}] {message}")

while True:
    time.sleep(1)
    try:
        if last_now != pytezos_cli.now():
            variables = {
                "engine_contract_address": ENGINE_ADDRESS,
                "ratio": (oracle.get_price().callback_view()*engine.storage['compound_interest_rate']()/10**24)*EMERGENCY_RATIO
            }
            response = requests.post(INDEXER_URL, json={'query': VAULT_COLLATERALIZATION_QUERY, 'variables': variables})
            operations = []
            current_token_balance = token.balance_of(requests=[{'owner':pytezos_cli.key.public_key_hash(), 'token_id':0}], callback=None).callback_view()[0]['balance']-1
            print(variables)
            print(response.json())
            for vault in response.json()['data']['vault']:
                amount_to_liquidate = min(int(1.6 * ((vault['minted']*engine.storage['compound_interest_rate']()/10**12) - (vault['balance']/3*(10**12/oracle.get_price().callback_view())))) - 10**6, current_token_balance)
                mutez_received = amount_to_liquidate*oracle.get_price().callback_view()/10**18

                if mutez_received > 1:
                    try:
                        print("liquidating {} with {} receiving {}".format(vault['owner'], amount_to_liquidate, mutez_received))
                        engine.liquidate(vault_owner=vault['owner'], token_amount=amount_to_liquidate).send(min_confirmations=1)
                    except:
                        print("failed")
            print("nothing to do for {}...".format(pytezos_cli.key.public_key_hash()))
            last_now = pytezos_cli.now()

    except Exception as e:
        traceback.print_exc()
        log(f"something went wrong: {e}")
