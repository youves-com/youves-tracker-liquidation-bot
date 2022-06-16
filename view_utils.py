from pytezos import pytezos, ContractInterface
from settings import RPC_ENDPOINT

pytezos_client = pytezos.using(shell = RPC_ENDPOINT)

def run_code(
    chain_id: str,
    parameter: dict,
    storage: dict,
    storage_type: dict,
    parameter_type: dict,
    result_type: dict,
    code: dict,
):
    """
    Run Michelson code and return the resultant stack.
    """
    query = {
        "script": [
            {
                "prim": 'parameter',
                "args": [
                    {
                        "prim": "pair",
                        "args": [
                            parameter_type,
                            storage_type
                        ]
                    }
                ],
            },
            {
                "prim": 'storage',
                "args": [
                    {
                        "prim": "option",
                        "args": [
                            result_type
                        ]
                    }
                ],
            },
            {
                "prim": 'code',
                "args": [
                    [
                        {
                            "prim": "CAR"
                        },
                        code,
                        { "prim": 'SOME' },
                        {
                            "prim": "NIL",
                            "args": [
                                {
                                    "prim": "operation"
                                }
                            ]
                        },
                        {
                            "prim": "PAIR"
                        }
                    ]
                ]
            }
        ],
        "storage": {
            "prim": "None"
        },
        "input": { "prim": "Pair", "args": [parameter, storage] },
        "amount": '0',
        "chain_id": chain_id,
        "balance": '0',
        "unparsing_mode": 'Optimized_legacy',
    }

    return pytezos_client.shell.head.helpers.scripts.run_code.post(query)


def get_oracle_price(oracle: ContractInterface) -> int:
    """
    Call 'get_price' on-chain view and extract the price from the result.

    Attributes:
        :param oracle: A proxy class for interacting with the oracle contract.
    """
    get_price_view = oracle.get_price
    view_name = list(filter(lambda view: view.endswith("price"), oracle.views.keys()))[0]
    if view_name == "view_price":
        get_price_view = oracle.view_price

    storage_type = oracle.storage.context.storage_expr["args"][0]
    result_type = get_price_view.return_ty_expr
    parameter_type = get_price_view.param_ty_expr
    code = get_price_view.code_expr
    result = run_code(
        chain_id        = oracle.context.get_chain_id(),
        parameter       = {"prim": "Unit"},
        storage         = oracle.storage.to_micheline(),
        storage_type    = storage_type,
        parameter_type  = parameter_type,
        result_type     = result_type,
        code            = code,
    )
    return int(result["storage"]["args"][0]["int"])
