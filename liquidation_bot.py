import time
import requests
from pytezos import pytezos, Key
import traceback
import settings
from view_utils import get_oracle_price

class LiquidationBot():
    """
    A bot that automates the tasks necessary to verify trigger conditions
    and interact directly with the smart contracts.

    Attributes:
        :param rpc_endpoint: RPC node uri.
        :param private_key: A private key to sign bot operations.
        :param engine_address: Address of the engine contract.
        :param oracle_address: Address of the price oracle contract.
        :param token_address: Address of the token contract.
        :param emergency_ratio: Emergency collateral ratio.
    """
    def __init__(
        self,
        tzkt_endpoint: str,
        rpc_endpoint: str,
        private_key: str,
        engine_address: str,
        oracle_address: str,
        token_address: str,
        emergency_ratio: float
    ):
        self.tzkt_endpoint = tzkt_endpoint
        self.emergency_ratio = emergency_ratio

        # Create a PyTezos client instance
        self.client = pytezos.using(shell=rpc_endpoint, key=Key.from_encoded_key(key=private_key))
        self.public_key_hash = self.client.key.public_key_hash()

        self.engine = self.client.contract(engine_address)
        self.oracle = self.client.contract(oracle_address)
        self.token = self.client.contract(token_address)

        self.previous_now = 0

    def run(self) -> None:
        """
        Check and liquidate vaults that are open to step in.
        """
        try:
            if self.has_new_head():
                # Fetch the latest price from the oracle
                oracle_price = self.oracle_price()
                # compound_interest_rate = self.engine.storage['compound_interest_rate']()
                # ratio = (oracle_price * compound_interest_rate / 10**24) * self.emergency_ratio
                current_token_balance = self.token.balance_of(
                    requests = [
                        {
                            'owner'     : self.public_key_hash,
                            'token_id'  : 0
                        }
                    ],
                    callback = None
                ).callback_view()[0]['balance']-1
                for vault in self.vaults():
                    minted = int(vault["value"]["minted"])
                    balance = int(vault["value"]["balance"])
                    oracle_price = self.oracle_price()
                    amount_to_liquidate = min(int(1.6 * ((minted*self.engine.storage['compound_interest_rate']()/10**12) - (balance/3*(10**12/oracle_price)))) - 10**6, current_token_balance)
                    mutez_received = amount_to_liquidate*oracle_price/10**18

                    if mutez_received > 1:
                        try:
                            self.log(vault)
                            self.log(f"Liquidating {vault['key']} with {amount_to_liquidate} receiving {mutez_received}.")
                            self.engine.liquidate(vault_owner=vault['key'], token_amount=amount_to_liquidate).send(min_confirmations=1)
                        except Exception as e:
                            self.log(f"failed with: {e}")

                self.log(f"nothing to do for {self.public_key_hash}...")

                self.previous_now = self.now()
        except Exception as e:
            traceback.print_exc()
            self.log(f"something went wrong: {e}")

    def vaults(self):
        """
        Get engine vaults from tzkt API.
        """
        vaults = requests.get(f"{self.tzkt_endpoint}/contracts/{self.engine.address}/bigmaps/vault_contexts/keys?limit=10000")
        return vaults.json()

    def oracle_price(self) -> int:
        """
        Get the latest price provisioned in the oracle contract.
        """
        return get_oracle_price(self.oracle)

    def has_new_head(self) -> bool:
        """
        Check if head block changed.
        """
        return self.previous_now != self.now()

    def now(self) -> int:
        """
        Get the timestamp of the latest block.
        """
        return self.client.now()

    def log(self, message) -> None:
        """
        Log bot information.

        Attributes:
            :param message: Message to log.
        """
        print(f"[{int(time.time())}:{self.__class__.__name__}] {message}")


bot = LiquidationBot(
    tzkt_endpoint   = settings.TZKT_ENDPOINT,
    rpc_endpoint    = settings.RPC_ENDPOINT,
    private_key     = settings.PRIVATE_KEY,
    engine_address  = settings.ENGINE_ADDRESS,
    oracle_address  = settings.TARGET_PRICE_ORACLE_ADDRESS,
    token_address   = settings.TOKEN_ADDRESS,
    emergency_ratio = settings.EMERGENCY_RATIO
)
while True:
    time.sleep(10)
    bot.run()
