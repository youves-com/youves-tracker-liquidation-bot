import requests
import logging
from decimal import Decimal
from pytezos import pytezos, Key
import settings
from view_utils import get_oracle_price

# Prepare logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

TARGET_COLLATERAL_RATIO = 3 # 300%

class LiquidationBot():
    """
    A bot that verifies if vaults are open to step-ins and liquidates them.

    Attributes:
        :param name: Bot identifier.
        :param rpc_endpoint: RPC node uri.
        :param private_key: A private key to sign bot operations.
        :param tzkt_endpoint: TZKT API uri.
        :param engine_address: Address of the engine contract.
        :param oracle_address: Address of the price oracle contract.
        :param collateral_token_decimals: Position of the decimal point in collateral token balances.
        :param token_decimals: Position of the decimal point in token balances.
        :param emergency_ratio: Emergency collateral ratio.
        :param minimum_reward: Minimum expected reward from liquidations.
    """
    def __init__(
        self,
        name: str,
        rpc_endpoint: str,
        private_key: str,
        tzkt_endpoint: str,
        engine_address: str,
        oracle_address: str,
        collateral_token_decimals: int,
        token_decimals: int,
        emergency_ratio: float,
        minimum_reward: float
    ):
        self.name = name
        self.tzkt_endpoint = tzkt_endpoint
        self.emergency_ratio = Decimal(emergency_ratio)
        self.minimum_reward = Decimal(minimum_reward)
        self.token_decimals = Decimal(token_decimals)
        self.collateral_token_decimals = Decimal(collateral_token_decimals)

        # Create a PyTezos client instance
        self.client = pytezos.using(shell=rpc_endpoint, key=Key.from_encoded_key(key=private_key))
        self.public_key_hash = self.client.key.public_key_hash()

        # Create interfaces to interact with contracts
        self.engine = self.client.contract(engine_address)
        self.oracle = self.client.contract(oracle_address)
        self.token = self.client.contract(self.engine.storage["token_contract"]())
        self.token_id = self.engine.storage["token_id"]()

        # Set initial block timestamp to 0.
        # It will be updated inside the `run` method.
        self.previous_now = 0

    def run(self) -> None:
        """
        Check and liquidate vaults that are open to step in.
        """
        try:
            if self.has_new_head():
                # Cache values
                target_price = self.oracle_price()
                token_balance = self.token_balance()
                tez_balance = self.client.balance()
                compound_interest_rate = Decimal(self.engine.storage['compound_interest_rate']())

                did_any_liquidation = False
                for vault in self.vaults():
                    is_being_liquidated = vault["value"]["is_being_liquidated"]
                    minted = Decimal(vault["value"]["minted"])
                    balance = Decimal(vault["value"]["balance"])

                    # The vault must have some token amount minted
                    if minted == 0:
                        continue

                    token_factor = 10**self.token_decimals
                    minted_synthetic_asset = minted * compound_interest_rate / token_factor
                    collateral_ratio = (balance / minted_synthetic_asset / target_price) * token_factor * 100

                    # Step-in is only allowed when the collateral ratio is less or equal
                    # to 200%, or if the vault is already being liquidated.
                    if not is_being_liquidated and collateral_ratio > self.emergency_ratio:
                        continue

                    self.debug(f"Found vault '{vault['key']}' with collateral ratio ({(collateral_ratio):.2f}%). (is_being_liquidated: {is_being_liquidated})")

                    # Compute the amount to be liquidated
                    amount_to_liquidate = self.amount_to_liquidate(balance, minted_synthetic_asset, target_price)
                    amount_to_liquidate = int(min(amount_to_liquidate, token_balance))
                    tez_to_receive = self.liquidation_reward_in_tez(amount_to_liquidate, target_price)

                    if tez_to_receive >= self.minimum_reward:
                        self.info(f"Liquidating {vault['key']}")
                        self.info(f"Amount to liquidate: {amount_to_liquidate}")
                        self.info(f"Liquidation reward: {tez_to_receive:.5f} ꜩ")
                        err = self.liquidate_vault(vault["key"], amount_to_liquidate)
                        if err is None:
                            self.info(f"Tez balance before liquidation: {tez_balance} ꜩ")
                            tez_balance = self.client.balance()
                            self.info(f"Tez balance after liquidation: {self.client.balance()} ꜩ")

                            self.info(f"Token balance before liquidation: {token_balance}")
                            token_balance = self.token_balance()
                            self.info(f"Token balance after liquidation: {token_balance}\n")

                            # Set to True to inform that at least one liquidation was successful
                            did_any_liquidation = True
                        else:
                            self.error(f"Liquidating failed with: {err}.")
                    else:
                        self.debug(f"Ignoring liquidation, amount ({tez_to_receive:.5f} ꜩ) it too low...")

                if not did_any_liquidation:
                    self.debug("Nothing to do...")

                # Set a new high water mark
                self.previous_now = self.now()

        except Exception as ex:
            self.error(f"Something went wrong: {ex}.")

    def vaults(self):
        """
        Get engine vaults from tzkt API.
        """
        vaults = requests.get(f"{self.tzkt_endpoint}/contracts/{self.engine.address}/bigmaps/vault_contexts/keys?limit=10000")
        return vaults.json()

    def amount_to_liquidate(
        self,
        balance: Decimal,
        minted_synthetic_asset: Decimal,
        target_price: Decimal
    ) -> Decimal:
        """
        Compute the amount to liquidate.

        Attributes:
            :param balance: Collateral amount in the vault.
            :param minted_synthetic_asset: Minted amount in the vault.
            :param target_price: Quote price.
        """
        collateral_token_factor = 10**self.collateral_token_decimals
        token_factor = 10**self.token_decimals
        excess_minted_amount = (minted_synthetic_asset - (balance / TARGET_COLLATERAL_RATIO * (token_factor / target_price))) - collateral_token_factor
        # 1.6 <=> (1 + step bonus)
        return excess_minted_amount * Decimal(1.6)

    def liquidation_reward_in_tez(self, amount_to_liquidate: Decimal, target_price: Decimal) -> Decimal:
        """
        Compute liquidation reward in ꜩ.

        Attributes:
            :param amount_to_liquidate: Synthetic token amount to be liquidated.
            :param target_price: Quote price.
        """
        bonus = Decimal(1.125) # TODO (Maybe this constant can be fetched from somewhere)
        return (amount_to_liquidate * target_price * bonus) / (10**(self.token_decimals+self.collateral_token_decimals))

    def liquidate_vault(self, vault_owner: str, amount_to_liquidate: Decimal):
        """
        Perform a liquidation on a vault.

        Attributes:
            :param vault_owner: The vault owner.
            :param amount_to_liquidate: Synthetic token amount to be liquidated.
        """
        try:
            self.engine.liquidate(vault_owner=vault_owner, token_amount=amount_to_liquidate).send(min_confirmations=1)
        except Exception as ex:
            return ex

    def token_balance(self) -> Decimal:
        """
        Get the current token amount owned by this account.
        """
        balance = self.token.balance_of(
            requests = [
                {
                    'owner'     : self.public_key_hash,
                    'token_id'  : self.token_id
                }
            ],
            callback = None
        ).callback_view()[0]['balance']-1
        return Decimal(balance)

    def oracle_price(self) -> Decimal:
        """
        Get the latest price provisioned in the oracle contract.
        """
        return Decimal(get_oracle_price(self.oracle))

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

    def info(self, message) -> None:
        logger.info("%s\t%s", self.name, message)

    def debug(self, message) -> None:
        logger.debug("%s\t%s", self.name, message)

    def error(self, message) -> None:
        logger.error("%s\t%s", self.name, message)


bot = LiquidationBot(
    name                        = settings.ENGINE_ADDRESS, # Use engine address as bot name (Used in the logs)
    tzkt_endpoint               = settings.TZKT_ENDPOINT,
    rpc_endpoint                = settings.RPC_ENDPOINT,
    private_key                 = settings.PRIVATE_KEY,
    engine_address              = settings.ENGINE_ADDRESS,
    oracle_address              = settings.TARGET_PRICE_ORACLE_ADDRESS,
    collateral_token_decimals   = settings.COLLATERAL_TOKEN_DECIMALS,
    token_decimals              = settings.TOKEN_DECIMALS,
    emergency_ratio             = settings.EMERGENCY_RATIO,
    minimum_reward              = settings.MINIMUM_REWARD
)

bot.info("Initialized...")
while True:
    bot.run()
