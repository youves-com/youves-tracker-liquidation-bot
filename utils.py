from pytezos import PyTezosClient, pytezos
from settings import RPC_ENDPOINT

pytezos_client = pytezos.using(shell = RPC_ENDPOINT)

def run_operation(client: PyTezosClient, destination, parameters):
    """
    Simulate an operation against the current chain state.
    """
    null_address = "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"
    fake_signature = "sigUHx32f9wesZ1n2BWpixXz4AQaZggEtchaQNHYGRCoWNAXx45WGW2ua3apUUUAGMLPwAU41QoaFCzVSL61VaessLg4YbbP"

    head = client.shell.head.header()
    counter = int(client.account(null_address)["counter"]) + 1

    query = {
        "chain_id": head["chain_id"],
        "operation": {
            "branch": head["hash"],
            "contents": [
                {
                    "kind": "transaction",
                    "fee": "999999",
                    "gas_limit": "1040000",
                    "storage_limit": "60000",
                    "amount": "0",
                    "source": null_address,
                    "counter": str(counter),
                    "destination": destination,
                    "parameters": parameters
                }
            ],
            "signature": fake_signature,
        }
    }

    return client.shell.head.helpers.scripts.run_operation.post(query)
