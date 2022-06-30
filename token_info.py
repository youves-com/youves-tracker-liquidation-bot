class Token:
    xtz         = "xtz"
    uUSD        = "uUSD"
    uDEFI       = "uDEFI"
    uBTC        = "uBTC"
    tzBTC       = "tzBTC"
    tzBTC_LB    = "tzBTC_LB"

vault_engines = {
    Token.uUSD: {
        Token.xtz: {
            "engine_address"                : "KT1FFE2LC5JpVakVjHm5mM36QVp2p3ZzH4hH",
            "target_oracle_decimals"        : 6,
            "min_token_amount_treshold"     : 1000
        },
        Token.tzBTC: {
            "engine_address"                : "KT1HxgqnVjGy7KsSUTEsQ6LgpD5iKSGu7QpA",
            "target_oracle_decimals"        : 12,
            "min_token_amount_treshold"     : 1
        },
        Token.tzBTC_LB: {
            "engine_address"               : "KT1FzcHaNhmpdYPNTgfb8frYXx7B5pvVyowu",
            "target_oracle_decimals"       : 6,
            "min_token_amount_treshold"    : 1
        }
    },
    Token.uDEFI: {
        Token.uUSD: {
            "engine_address"                : "KT1B2GSe47rcMCZTRk294havTpyJ36JbgdeB",
            "target_oracle_decimals"        : 6,
            "min_token_amount_treshold"     : 1000000000
        },
        Token.xtz: {
            "engine_address"                : "KT1LQcsXGpmLXnwrfftuQdCLNvLRLUAuNPCV",
            "target_oracle_decimals"        : 6,
            "min_token_amount_treshold"     : 1000
        },
        Token.tzBTC_LB: {
            "engine_address"                : "KT1E45AvpSr7Basw2bee3g8ri2LK2C2SV2XG",
            "target_oracle_decimals"        : 6,
            "min_token_amount_treshold"     : 1
        }
    },
    Token.uBTC: {
        Token.xtz: {
            "engine_address"                : "KT1VjQoL5QvyZtm9m1voQKNTNcQLi5QiGsRZ",
            "target_oracle_decimals"        : 6,
            "min_token_amount_treshold"     : 1000,
        },
        Token.tzBTC_LB: {
            "engine_address"                : "KT1NFWUqr9xNvVsz2LXCPef1eRcexJz5Q2MH",
            "target_oracle_decimals"        : 6,
            "min_token_amount_treshold"     : 1
        }
    }
}

decimals_lookup = {
    Token.xtz       : 6,
    Token.uUSD      : 12,
    Token.uDEFI     : 12,
    Token.uBTC      : 12,
    Token.tzBTC     : 8,
    Token.tzBTC_LB  : 0
}

def get_decimals_for_ratio(collateral_token: Token, syntetic_token_decimals):
    if collateral_token == Token.tzBTC:
        return 10
    elif collateral_token == Token.xtz:
        return syntetic_token_decimals
    elif collateral_token == Token.tzBTC_LB:
        return 6 + syntetic_token_decimals

    return 6 # default
