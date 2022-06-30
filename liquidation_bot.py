import traceback
import requests
import logging
from pytezos import pytezos, Key
import settings
from utils import run_operation
from token_info import decimals_lookup, vault_engines, get_decimals_for_ratio

# Prepare logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

class LiquidationBot():
    """
    A bot that verifies if vaults are open to step-ins and liquidates them.

    Attributes:
        :param name: Bot identifier.
        :param rpc_endpoint: RPC node uri.
        :param private_key: A private key to sign bot operations.
        :param tzkt_endpoint: TZKT API uri.
        :param collateral_token
        :param synthetic_asset_token
        :param minimum_payout: Minimum expected payout from liquidations (In collateral token units).
        :param step_in_ratio: 1 + step_bonus
    """
    def __init__(
        self,
        name: str,
        rpc_endpoint: str,
        private_key: str,
        tzkt_endpoint: str,
        collateral_token: str,
        synthetic_asset_token: str,
        minimum_payout: float,
        step_in_ratio: float
    ):
        self.name = name
        self.tzkt_endpoint = tzkt_endpoint
        self.synthetic_asset_token = synthetic_asset_token
        self.collateral_token = collateral_token
        self.minimum_payout = minimum_payout
        self.step_in_ratio = step_in_ratio
        self.token_decimals = decimals_lookup[synthetic_asset_token]
        self.target_oracle_decimals = vault_engines[synthetic_asset_token][collateral_token]["target_oracle_decimals"]
        self.min_token_amount_treshold = vault_engines[synthetic_asset_token][collateral_token]["min_token_amount_treshold"]

        if self.minimum_payout < self.min_token_amount_treshold:
            self.error(f"MINIMUM_PAYOUT must be higher than: {self.min_token_amount_treshold}")
            exit(1)

        # Create a PyTezos client instance
        self.client = pytezos.using(shell=rpc_endpoint, key=Key.from_encoded_key(key=private_key))
        self.public_key_hash = self.client.key.public_key_hash()

        # Create interfaces to interact with contracts
        self.engine = self.client.contract(vault_engines[synthetic_asset_token][collateral_token]["engine_address"])
        self.oracle = self.client.contract(self.engine.storage["target_price_oracle"]())
        self.token = self.client.contract(self.engine.storage["token_contract"]())
        self.token_id = self.engine.storage["token_id"]()

        # In V3 engine this value will be provided from `self.engine.storage['liquidation_payout_ratio']()`
        self.liquidation_payout_ratio = 1.125
        # In V3 engine this value will be provided from `self.engine.storage['settlement_reward_fee_ratio']()`
        self.settlement_reward_fee_ratio = 0.125
        # In V3 engine this value will be provided from `self.engine.storage['collateral_ratio']()`
        self.collateral_ratio = 2
        # In V3 engine this value will be provided from `self.engine.storage['settlement_ratio']()`
        self.settlement_ratio = 3

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
                token_balance = self.token_balance()
                compound_interest_rate = int(self.engine.storage['compound_interest_rate']())
                # If token_decimals is not 6, we need to normalize the price. (6 decimals was the default)
                target_price = self.oracle_price() * (10 ** (-1 * (self.target_oracle_decimals - 6)))

                did_any_liquidation = False
                for vault in self.vaults():
                    minted = int(vault["value"]["minted"])
                    balance = int(vault["value"]["balance"])

                    # The vault must have some token amount minted
                    if minted == 0:
                        continue

                    minted_synthetic_asset = (minted * compound_interest_rate) // 10**self.token_decimals
                    precision_factor = 10**get_decimals_for_ratio(self.collateral_token, self.token_decimals)
                    collateral_ratio = ((balance / target_price) / minted_synthetic_asset) * precision_factor

                    # Step-in is only allowed when the collateral ratio is less or equal to 200%.
                    # Also, a vault with a collateral ratio of <=100% makes it impossible to do a profitable step in.
                    if collateral_ratio > self.collateral_ratio or collateral_ratio <= 1:
                        continue

                    self.debug(f"Found vault '{vault['key']}' with collateral ratio ({(collateral_ratio*100):.2f}%).")

                    # Compute the amount to be liquidated
                    amount_to_liquidate = self.amount_to_liquidate(balance, minted_synthetic_asset, target_price)
                    amount_to_liquidate = min(amount_to_liquidate, token_balance)
                    payout_amount = self.liquidation_payout(amount_to_liquidate, target_price)

                    if payout_amount >= self.minimum_payout:
                        self.info(f"Liquidating {vault['key']}")
                        self.info(f"Amount to liquidate: {amount_to_liquidate} {self.synthetic_asset_token}")
                        self.info(f"Liquidation payout: {payout_amount} {self.collateral_token}")

                        err = self.liquidate_vault(vault["key"], amount_to_liquidate)
                        if err is None:
                            self.info(f"Token balance before liquidation: {token_balance}")
                            token_balance = self.token_balance()
                            self.info(f"Token balance after liquidation: {token_balance}\n")

                            # Set to True to inform that at least one liquidation was successful
                            did_any_liquidation = True
                        else:
                            self.error(f"Liquidating failed with: {err}.")
                    else:
                        self.debug(f"Ignoring liquidation, payout ({payout_amount} {self.collateral_token}) is too low...")

                if not did_any_liquidation:
                    self.debug("Nothing to do...")

                # Set a new high water mark
                self.previous_now = self.now()

        except Exception as ex:
            traceback.print_exc()
            self.error(f"Something went wrong: {ex}.")

    def vaults(self):
        """
        Get engine vaults from tzkt API.
        """
        vaults = requests.get(f"{self.tzkt_endpoint}/contracts/{self.engine.address}/bigmaps/vault_contexts/keys?limit=10000")
        return vaults.json()

    def amount_to_liquidate(
        self,
        balance,
        minted_synthetic_asset,
        target_price
    ) -> int:
        """
        Compute the amount to liquidate.

        Attributes:
            :param balance: Collateral amount in the vault.
            :param minted_synthetic_asset: Minted amount in the vault.
            :param target_price: Quote price.
        """
        precision_factor = 10**get_decimals_for_ratio(self.collateral_token, self.token_decimals)
        expected_minted_amount = ((balance * (precision_factor / target_price)) / self.settlement_ratio)
        excess_minted_amount = (minted_synthetic_asset - expected_minted_amount)
        return int(excess_minted_amount * self.step_in_ratio)

    def liquidation_payout(self, amount_to_liquidate, target_price) -> int:
        """
        Compute liquidation reward in ꜩ.

        Attributes:
            :param amount_to_liquidate: Synthetic token amount to be liquidated.
            :param target_price: Quote price.
        """
        precision_factor = 10**get_decimals_for_ratio(self.collateral_token, self.token_decimals)
        return int((amount_to_liquidate * target_price * self.liquidation_payout_ratio) / precision_factor)

    def liquidate_vault(self, vault_owner: str, amount_to_liquidate: int):
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

    def token_balance(self) -> int:
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
        return int(balance)

    def oracle_price(self) -> int:
        """
        Get the latest price provisioned in the oracle contract.
        """

        valid_nat_callback = "KT1Lj4y492KN1zDyeeKR2HG74SR2j5tcenMV"

        result = run_operation(
            self.client,
            self.oracle.address,
            {
                "entrypoint": 'get_price',
                "value": {
                    "string": valid_nat_callback
                }
            }
        )

        try:
            result = result["contents"][0]["metadata"]["internal_operation_results"].pop()
            return int(result["result"]["storage"]["int"])
        except Exception as ex:
            raise Exception('Could not fetch oracle price.') from ex

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
    name                        = f"{settings.SYNTHETIC_ASSET_TOKEN}_{settings.COLLATERAL_TOKEN}",
    tzkt_endpoint               = settings.TZKT_ENDPOINT,
    rpc_endpoint                = settings.RPC_ENDPOINT,
    private_key                 = settings.PRIVATE_KEY,
    collateral_token            = settings.COLLATERAL_TOKEN,
    synthetic_asset_token       = settings.SYNTHETIC_ASSET_TOKEN,
    minimum_payout              = settings.MINIMUM_PAYOUT,
    step_in_ratio               = settings.STEP_IN_RATIO
)

bot.info("Initialized...")
while True:
    bot.run()
