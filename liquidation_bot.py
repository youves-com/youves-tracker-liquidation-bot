import time
import requests
from pytezos import pytezos, Key
import traceback
import settings
from view_utils import get_oracle_price

PRICE_PRECISION_FACTOR = 10**6
LIQUIDATION_REWARD_BITSHIFT = 3

def compute_liquidation_tez_amount(token_amount, target_price):
    token_amount_market_value = token_amount * target_price
    liquidation_reward = token_amount_market_value >> LIQUIDATION_REWARD_BITSHIFT
    return (token_amount_market_value + liquidation_reward) / PRICE_PRECISION_FACTOR

class LiquidationBot():
    """
    A bot that verifies if vaults are open to step-ins and liquidates them.

    Attributes:
        :param rpc_endpoint: RPC node uri.
        :param private_key: A private key to sign bot operations.
        :param tzkt_endpoint: TZKT API uri.
        :param engine_address: Address of the engine contract.
        :param oracle_address: Address of the price oracle contract.
        :param emergency_ratio: Emergency collateral ratio.
        :param minimum_reward: Minimum expected reward from liquidations.
    """
    def __init__(
        self,
        rpc_endpoint: str,
        private_key: str,
        tzkt_endpoint: str,
        engine_address: str,
        oracle_address: str,
        emergency_ratio: float,
        minimum_reward: float
    ):
        self.tzkt_endpoint = tzkt_endpoint
        self.emergency_ratio = emergency_ratio
        self.minimum_reward = minimum_reward

        # Create a PyTezos client instance
        self.client = pytezos.using(shell=rpc_endpoint, key=Key.from_encoded_key(key=private_key))
        self.public_key_hash = self.client.key.public_key_hash()

        # Create interfaces to interact with contracts
        self.engine = self.client.contract(engine_address)
        self.oracle = self.client.contract(oracle_address)
        self.token = self.client.contract(self.engine.storage["token_contract"]())
        self.token_id = self.engine.storage["token_id"]()

        self.token_metadata = self.token._get_token_metadata_from_storage(self.token_id)
        self.token_precison_factor = 10 ** int(self.token_metadata.decimals)

        # Set initial block timestamp to 0.
        # It will be updated inside the `run` method.
        self.previous_now = 0

    def run(self) -> None:
        """
        Check and liquidate vaults that are open to step in.
        """
        self.log("---")
        try:
            if self.has_new_head():
                # Fetch the latest price from the oracle
                oracle_price = self.oracle_price()

                for vault in self.vaults():
                    minted = int(vault["value"]["minted"])
                    balance = int(vault["value"]["balance"])
                    is_being_liquidated = int(vault["value"]["is_being_liquidated"])
                    compound_interest_rate = self.engine.storage['compound_interest_rate']()
                    current_token_amount = (minted*compound_interest_rate) / self.token_precison_factor

                    # (This may change in engine v3)
                    #
                    # Skip if emergency ratio has not been reached
                    # and if vault is not being liquidated
                    if (not is_being_liquidated and balance * PRICE_PRECISION_FACTOR < current_token_amount*oracle_price*self.emergency_ratio):
                        continue

                    # Compute the amount to be liquidated
                    liquidation_threshold = int(1.6 * ((minted*compound_interest_rate/self.token_precison_factor) - (balance/3*(self.token_precison_factor/oracle_price)))) - PRICE_PRECISION_FACTOR
                    amount_to_liquidate = min(liquidation_threshold, self.token_balance())
                    tez_to_receive = compute_liquidation_tez_amount(amount_to_liquidate, oracle_price)

                    if tez_to_receive > self.minimum_reward:
                        try:
                            self.log(f"Liquidating {vault['key']}")
                            self.log(f"Amount being liquidated: {amount_to_liquidate / self.token_precison_factor}{self.token_metadata.symbol}")
                            self.log(f"Liquidation reward: {tez_to_receive}ꜩ")
                            self.log(f"Balance before liquidation: {self.client.balance()}")
                            self.engine.liquidate(vault_owner=vault['key'], token_amount=amount_to_liquidate).send(min_confirmations=1)
                            self.log(f"Balance after liquidation: {self.client.balance()}")
                        except Exception as ex:
                            self.log(f"Liquidating failed with: {ex}.")

                # Set a new high water mark
                self.previous_now = self.now()

        except Exception as ex:
            self.log(f"Something went wrong: {ex}.")
            if settings.DEBUG:
                traceback.print_exc()

    def vaults(self):
        """
        Get engine vaults from tzkt API.
        """
        vaults = requests.get(f"{self.tzkt_endpoint}/contracts/{self.engine.address}/bigmaps/vault_contexts/keys?limit=10000")
        return vaults.json()

    def token_balance(self):
        """
        Get the current token amount owned by this account.
        """
        return self.token.balance_of(
            requests = [
                {
                    'owner'     : self.public_key_hash,
                    'token_id'  : self.token_id
                }
            ],
            callback = None
        ).callback_view()[0]['balance']

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
    emergency_ratio = settings.EMERGENCY_RATIO,
    minimum_reward  = settings.MINIMUM_REWARD
)
while True:
    bot.run()
    # Wait 10 seconds before each run
    time.sleep(10)
