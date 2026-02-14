#!/usr/bin/env python3
"""
查询合约特定操作的最近用户地址
支持按方法过滤、时间排序、数量限制、ABI 解码
"""

import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional, List, Dict, Tuple, Any


# Etherscan API V2 统一端点
ETHERSCAN_V2_ENDPOINT = "https://api.etherscan.io/v2/api"


# ============== ABI 解码功能 ==============

# 常用方法 ABI 定义 (方法签名 -> 参数类型列表)
METHOD_ABIS = {
    # ERC20
    "0xa9059cbb": {  # transfer
        "name": "transfer",
        "params": [("to", "address"), ("amount", "uint256")],
        "decimals_param": "amount"
    },
    "0x095ea7b3": {  # approve
        "name": "approve",
        "params": [("spender", "address"), ("amount", "uint256")],
        "decimals_param": "amount"
    },
    "0x23b872dd": {  # transferFrom
        "name": "transferFrom",
        "params": [("from", "address"), ("to", "address"), ("amount", "uint256")],
        "decimals_param": "amount"
    },

    # Lido
    "0xa1903eab": {  # submit
        "name": "submit",
        "params": [("referral", "address")],
    },
    "0xd6681042": {  # requestWithdrawals
        "name": "requestWithdrawals",
        "params": [("amounts", "uint256[]"), ("owner", "address")],
    },

    # Everstake
    "0x3a29dbae": {  # stake
        "name": "stake",
        "params": [("amount", "uint64")],
        "decimals_param": "amount"
    },
    "0x2e17de78": {  # unstake
        "name": "unstake",
        "params": [("amount", "uint256")],
        "decimals_param": "amount"
    },

    # WETH
    "0xd0e30db0": {  # deposit
        "name": "deposit",
        "params": [],
    },
    "0x2e1a7d4d": {  # withdraw
        "name": "withdraw",
        "params": [("amount", "uint256")],
        "decimals_param": "amount"
    },

    # Uniswap V3
    "0x414bf389": {  # exactInputSingle
        "name": "exactInputSingle",
        "params": [
            ("tokenIn", "address"),
            ("tokenOut", "address"),
            ("fee", "uint24"),
            ("recipient", "address"),
            ("deadline", "uint256"),
            ("amountIn", "uint256"),
            ("amountOutMinimum", "uint256"),
            ("sqrtPriceLimitX96", "uint160")
        ],
    },

    # ============== Aave V3 ==============
    "0x617ba037": {  # supply
        "name": "supply",
        "params": [
            ("asset", "address"),
            ("amount", "uint256"),
            ("onBehalfOf", "address"),
            ("referralCode", "uint16")
        ],
        "decimals_param": "amount"
    },
    "0x69328dec": {  # withdraw
        "name": "withdraw",
        "params": [
            ("asset", "address"),
            ("amount", "uint256"),
            ("to", "address")
        ],
        "decimals_param": "amount"
    },
    "0xa415bcad": {  # borrow
        "name": "borrow",
        "params": [
            ("asset", "address"),
            ("amount", "uint256"),
            ("interestRateMode", "uint256"),
            ("referralCode", "uint16"),
            ("onBehalfOf", "address")
        ],
        "decimals_param": "amount"
    },
    "0x573ade81": {  # repay
        "name": "repay",
        "params": [
            ("asset", "address"),
            ("amount", "uint256"),
            ("interestRateMode", "uint256"),
            ("onBehalfOf", "address")
        ],
        "decimals_param": "amount"
    },
    "0xe8eda9df": {  # deposit (Aave V2)
        "name": "deposit",
        "params": [
            ("asset", "address"),
            ("amount", "uint256"),
            ("onBehalfOf", "address"),
            ("referralCode", "uint16")
        ],
        "decimals_param": "amount"
    },
    "0x00a718a9": {  # liquidationCall
        "name": "liquidationCall",
        "params": [
            ("collateralAsset", "address"),
            ("debtAsset", "address"),
            ("user", "address"),
            ("debtToCover", "uint256"),
            ("receiveAToken", "bool")
        ],
        "decimals_param": "debtToCover"
    },
    "0x42b0b77c": {  # flashLoan
        "name": "flashLoan",
        "params": [
            ("receiverAddress", "address"),
            ("assets", "address[]"),
            ("amounts", "uint256[]"),
            ("modes", "uint256[]"),
            ("onBehalfOf", "address"),
            ("params", "bytes"),
            ("referralCode", "uint16")
        ],
    },
    "0x1b11d0ff": {  # repayWithATokens
        "name": "repayWithATokens",
        "params": [
            ("asset", "address"),
            ("amount", "uint256"),
            ("interestRateMode", "uint256")
        ],
        "decimals_param": "amount"
    },
    "0x94ba89a2": {  # setUserUseReserveAsCollateral
        "name": "setUserUseReserveAsCollateral",
        "params": [
            ("asset", "address"),
            ("useAsCollateral", "bool")
        ],
    },

    # ============== Compound V2 (cToken) ==============
    "0xa0712d68": {  # mint
        "name": "mint",
        "params": [("mintAmount", "uint256")],
        "decimals_param": "mintAmount"
    },
    "0xdb006a75": {  # redeem
        "name": "redeem",
        "params": [("redeemTokens", "uint256")],
        "decimals_param": "redeemTokens"
    },
    "0x852a12e3": {  # redeemUnderlying
        "name": "redeemUnderlying",
        "params": [("redeemAmount", "uint256")],
        "decimals_param": "redeemAmount"
    },
    "0xc5ebeaec": {  # borrow
        "name": "borrow",
        "params": [("borrowAmount", "uint256")],
        "decimals_param": "borrowAmount"
    },
    "0x0e752702": {  # repayBorrow
        "name": "repayBorrow",
        "params": [("repayAmount", "uint256")],
        "decimals_param": "repayAmount"
    },
    "0x2608f818": {  # repayBorrowBehalf
        "name": "repayBorrowBehalf",
        "params": [
            ("borrower", "address"),
            ("repayAmount", "uint256")
        ],
        "decimals_param": "repayAmount"
    },
    "0xf5e3c462": {  # liquidateBorrow
        "name": "liquidateBorrow",
        "params": [
            ("borrower", "address"),
            ("repayAmount", "uint256"),
            ("cTokenCollateral", "address")
        ],
        "decimals_param": "repayAmount"
    },

    # ============== Compound V3 (Comet) ==============
    "0xf2b9fdb8": {  # supply
        "name": "supply",
        "params": [
            ("asset", "address"),
            ("amount", "uint256")
        ],
        "decimals_param": "amount"
    },
    "0xf3fef3a3": {  # withdraw
        "name": "withdraw",
        "params": [
            ("asset", "address"),
            ("amount", "uint256")
        ],
        "decimals_param": "amount"
    },
    "0x4232cd63": {  # supplyTo
        "name": "supplyTo",
        "params": [
            ("dst", "address"),
            ("asset", "address"),
            ("amount", "uint256")
        ],
        "decimals_param": "amount"
    },
    "0x2644131b": {  # withdrawTo
        "name": "withdrawTo",
        "params": [
            ("to", "address"),
            ("asset", "address"),
            ("amount", "uint256")
        ],
        "decimals_param": "amount"
    },
    "0x66de5e4b": {  # absorb
        "name": "absorb",
        "params": [
            ("absorber", "address"),
            ("accounts", "address[]")
        ],
    },
    "0xe4723589": {  # buyCollateral
        "name": "buyCollateral",
        "params": [
            ("asset", "address"),
            ("minAmount", "uint256"),
            ("baseAmount", "uint256"),
            ("recipient", "address")
        ],
    },
}

# 代币精度配置
TOKEN_DECIMALS = {
    # Stablecoins (6 decimals)
    "0xdac17f958d2ee523a2206206994597c13d831ec7": 6,   # USDT
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 6,   # USDC

    # ETH derivatives (18 decimals)
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 18,  # WETH
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": 18,  # stETH
    "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0": 18,  # wstETH
    "0xbe9895146f7af43049ca1c1ae358b0541ea49704": 18,  # cbETH
    "0xf951e335afb289353dc249e82926178eac7ded78": 18,  # swETH
    "0xac3e018457b222d93114458476f3e3416abbe38f": 18,  # sfrxETH

    # Other tokens (18 decimals)
    "0x6b175474e89094c44da98b954eedeac495271d0f": 18,  # DAI
    "0x5f98805a4e8be255a32880fdec7f6728c6568ba0": 18,  # LUSD
    "0x853d955acef822db058eb8505911ed77f175b99e": 18,  # FRAX
    "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": 18,  # USDe

    # BTC derivatives (8 decimals)
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": 8,   # WBTC
    "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf": 8,   # cbBTC

    # Other
    "0x514910771af9ca656af840dff83e8264ecf986ca": 18,  # LINK
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": 18,  # AAVE
    "0xc00e94cb662c3520282e6f5717214004a7f26888": 18,  # COMP

    # Compound V2 cTokens (使用 underlying 精度)
    "0x39aa39c021dfbae8fac545936693ac917d5e7563": 6,   # cUSDC -> USDC (6)
    "0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9": 6,   # cUSDT -> USDT (6)
    "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643": 18,  # cDAI -> DAI (18)
    "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5": 18,  # cETH -> ETH (18)
    "0xccf4429db6322d5c611ee964527d42e5d685dd6a": 8,   # cWBTC -> WBTC (8)
    "0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4": 18,  # cCOMP -> COMP (18)
    "0xface851a4921ce59e912d19329929ce6da6eb0c7": 18,  # cLINK -> LINK (18)
    "0x35a18000230da775cac24873d00ff85bccded550": 18,  # cUNI -> UNI (18)

    # Compound V3 Comet (使用 base asset 精度)
    "0xc3d688b66703497daa19211eedff47f25384cdc3": 6,   # Compound V3 USDC
    "0xa17581a9e3356d9a858b789d68b4d866e593ae94": 18,  # Compound V3 WETH
}


def decode_uint(data: str, bits: int = 256) -> int:
    """解码 uint 类型"""
    return int(data, 16)


def decode_address(data: str) -> str:
    """解码 address 类型 (取后 40 位)"""
    return "0x" + data[-40:].lower()


def decode_param(data: str, param_type: str) -> Any:
    """根据类型解码单个参数"""
    if param_type == "address":
        return decode_address(data)
    elif param_type.startswith("uint"):
        return decode_uint(data)
    elif param_type.startswith("int"):
        value = decode_uint(data)
        bits = int(param_type[3:]) if param_type[3:] else 256
        if value >= 2 ** (bits - 1):
            value -= 2 ** bits
        return value
    elif param_type == "bool":
        return decode_uint(data) != 0
    else:
        return data  # 未知类型返回原始数据


def decode_input_data(input_data: str, contract_address: str = "") -> Dict:
    """
    解码交易输入数据

    Args:
        input_data: 交易的 input 字段 (hex string)
        contract_address: 合约地址 (用于获取代币精度)

    Returns:
        解码后的数据字典
    """
    if not input_data or len(input_data) < 10:
        return {"method": "unknown", "params": {}}

    # 提取方法签名 (前 4 字节)
    method_sig = input_data[:10].lower()
    params_data = input_data[10:]

    # 查找 ABI 定义
    abi = METHOD_ABIS.get(method_sig)
    if not abi:
        return {
            "method": method_sig,
            "params": {"raw": params_data[:128] + "..." if len(params_data) > 128 else params_data}
        }

    decoded = {
        "method": abi["name"],
        "params": {}
    }

    # 先解码所有参数
    offset = 0
    for param_name, param_type in abi.get("params", []):
        if offset + 64 > len(params_data):
            break

        chunk = params_data[offset:offset + 64]
        value = decode_param(chunk, param_type)
        decoded["params"][param_name] = value
        offset += 64

    # 处理金额格式化 - 借贷协议使用 asset 地址的精度
    decimals_param = abi.get("decimals_param")
    if decimals_param and decimals_param in decoded["params"]:
        amount = decoded["params"][decimals_param]
        if isinstance(amount, int):
            # 优先使用 asset 参数的地址获取精度 (Aave/Compound 等借贷协议)
            asset_address = decoded["params"].get("asset", "")
            if asset_address and isinstance(asset_address, str):
                decimals = TOKEN_DECIMALS.get(asset_address.lower(), 18)
            else:
                decimals = TOKEN_DECIMALS.get(contract_address.lower(), 18)

            decoded["params"][f"{decimals_param}_formatted"] = round(amount / (10 ** decimals), 6)

    return decoded

# 各链的 Chain ID
CHAIN_IDS = {
    "ethereum": 1,
    "bsc": 56,
    "polygon": 137,
    "arbitrum": 42161,
    "optimism": 10,
    "base": 8453,
    "avalanche": 43114,
    "fantom": 250
}

# 常用合约地址
KNOWN_CONTRACTS = {
    # Lido
    "lido": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",           # Lido stETH
    "lido_withdrawal": "0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1", # Lido Withdrawal

    # Staking
    "everstake": "0xd523794c879d9ec028960a231f866758e405be34",      # Everstake ETH Staking

    # DEX
    "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "uniswap_v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",

    # Tokens
    "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "dai": "0x6B175474E89094C44Da98b954EescdedDAC495271d0F",
    "wbtc": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",

    # Aave V3 (Ethereum)
    "aave_v3": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",        # Aave V3 Pool
    "aave_v3_pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "aave_v2": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",        # Aave V2 Pool

    # Compound
    "compound_v3_usdc": "0xc3d688B66703497DAA19211EEdff47f25384cdc3",  # Compound V3 USDC (Comet)
    "compound_v3_weth": "0xA17581A9E3356d9A858b789D68B4d866e593aE94",  # Compound V3 WETH (Comet)
    "cusdc": "0x39AA39c021dfbaE8faC545936693aC917d5E7563",           # Compound V2 cUSDC
    "ceth": "0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5",            # Compound V2 cETH
    "cdai": "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",            # Compound V2 cDAI
}

# 常用方法签名 (前 4 字节)
METHOD_SIGNATURES = {
    # Lido
    "submit": "0xa1903eab",      # submit(address _referral) - Lido 质押
    "requestWithdrawals": "0xd6681042",  # requestWithdrawals

    # Everstake
    "stake": "0x3a29dbae",       # stake(uint64 _amount) - Everstake 质押
    "unstake": "0x2e17de78",     # unstake(uint256) - Everstake 解质押

    # ERC20
    "transfer": "0xa9059cbb",    # transfer(address,uint256)
    "approve": "0x095ea7b3",     # approve(address,uint256)
    "transferFrom": "0x23b872dd", # transferFrom(address,address,uint256)

    # Uniswap
    "swap": "0x5ae401dc",        # multicall (swap)
    "exactInputSingle": "0x414bf389",

    # General
    "deposit": "0xd0e30db0",     # deposit()
    "withdraw": "0x2e1a7d4d",    # withdraw(uint256)

    # Aave V3
    "supply": "0x617ba037",       # supply(address,uint256,address,uint16)
    "aave_withdraw": "0x69328dec", # withdraw(address,uint256,address)
    "borrow": "0xa415bcad",       # borrow(address,uint256,uint256,uint16,address)
    "repay": "0x573ade81",        # repay(address,uint256,uint256,address)
    "liquidate": "0x00a718a9",    # liquidationCall
    "flashloan": "0x42b0b77c",    # flashLoan
    "repayWithATokens": "0x1b11d0ff",

    # Aave V2
    "aave_v2_deposit": "0xe8eda9df",  # deposit(address,uint256,address,uint16)

    # Compound V2
    "mint": "0xa0712d68",         # mint(uint256)
    "redeem": "0xdb006a75",       # redeem(uint256)
    "redeemUnderlying": "0x852a12e3",
    "compound_borrow": "0xc5ebeaec",  # borrow(uint256)
    "repayBorrow": "0x0e752702",  # repayBorrow(uint256)
    "liquidateBorrow": "0xf5e3c462",

    # Compound V3
    "compound_supply": "0xf2b9fdb8",   # supply(address,uint256)
    "compound_withdraw": "0xf3fef3a3", # withdraw(address,uint256)
}


def get_api_key() -> str:
    """获取 Etherscan API Key"""
    return os.environ.get("ETHERSCAN_API_KEY", "")


def api_call(chain: str, params: dict, api_key: str) -> dict:
    """执行 Etherscan API V2 调用"""
    chain_id = CHAIN_IDS.get(chain)
    if not chain_id:
        raise Exception(f"Unsupported chain: {chain}")

    params["apikey"] = api_key
    params["chainid"] = chain_id
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{ETHERSCAN_V2_ENDPOINT}?{query}"

    req = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data
    except (HTTPError, URLError) as e:
        raise Exception(f"Request failed: {e}")


def get_recent_transactions(
    chain: str,
    contract: str,
    api_key: str,
    method: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """
    获取合约的最近交易

    Args:
        chain: 区块链网络
        contract: 合约地址
        api_key: API Key
        method: 可选，方法签名过滤（如 "submit", "transfer"）
        limit: 获取数量
    """
    params = {
        "module": "account",
        "action": "txlist",
        "address": contract,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": min(limit * 10, 10000),  # 多获取一些用于过滤
        "sort": "desc"  # 最新的在前
    }

    result = api_call(chain, params, api_key)
    txs = result.get("result", []) if isinstance(result.get("result"), list) else []

    # 按方法过滤
    if method:
        method_sig = METHOD_SIGNATURES.get(method, method)
        if not method_sig.startswith("0x"):
            method_sig = "0x" + method_sig
        txs = [tx for tx in txs if tx.get("input", "").startswith(method_sig)]

    return txs[:limit * 5]  # 返回足够的数据用于去重


def find_recent_users(
    chain: str,
    contract: str,
    api_key: str,
    method: Optional[str] = None,
    count: int = 5,
    unique: bool = True
) -> Dict:
    """
    查找合约的最近操作用户

    Args:
        chain: 区块链网络
        contract: 合约地址
        api_key: API Key
        method: 可选，方法名过滤
        count: 返回地址数量
        unique: 是否去重（默认 True）

    Returns:
        最近操作的用户地址列表
    """
    print(f"Fetching recent transactions for {contract}...", file=sys.stderr)
    if method:
        print(f"Filtering by method: {method}", file=sys.stderr)

    txs = get_recent_transactions(chain, contract, api_key, method, count * 20)

    if not txs:
        return {
            "contract": contract,
            "chain": chain,
            "method": method,
            "users": [],
            "total_found": 0
        }

    users = []
    seen_addresses = set()

    for tx in txs:
        from_addr = tx.get("from", "").lower()

        # 跳过失败的交易
        if tx.get("isError") == "1":
            continue

        # 去重
        if unique and from_addr in seen_addresses:
            continue

        seen_addresses.add(from_addr)

        # 解析时间
        timestamp = int(tx.get("timeStamp", 0))
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        # 解析 value (ETH)
        value_wei = int(tx.get("value", 0))
        value_eth = value_wei / 1e18

        # ABI 解码
        input_data = tx.get("input", "")
        decoded = decode_input_data(input_data, contract)

        user_data = {
            "address": from_addr,
            "tx_hash": tx.get("hash", ""),
            "time": time_str,
            "timestamp": timestamp,
            "value_eth": round(value_eth, 6),
            "method": decoded.get("method", tx.get("functionName", "").split("(")[0] or "unknown"),
            "block": int(tx.get("blockNumber", 0)),
            "decoded_params": decoded.get("params", {})
        }

        users.append(user_data)

        if len(users) >= count:
            break

    return {
        "contract": contract,
        "chain": chain,
        "method_filter": method,
        "users": users,
        "total_found": len(users)
    }


def main():
    parser = argparse.ArgumentParser(
        description="查询合约特定操作的最近用户地址"
    )
    parser.add_argument(
        "--chain",
        default="ethereum",
        choices=list(CHAIN_IDS.keys()),
        help="区块链网络 (默认: ethereum)"
    )
    parser.add_argument(
        "--contract",
        required=True,
        help="合约地址或名称 (支持: lido, usdt, usdc, weth, uniswap_v3_router)"
    )
    parser.add_argument(
        "--method",
        help="方法名过滤 (如: submit, transfer, deposit, withdraw)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="返回地址数量 (默认: 5)"
    )
    parser.add_argument(
        "--api-key",
        help="Etherscan API Key"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="显示所有交易（不去重地址）"
    )

    args = parser.parse_args()

    # 解析合约地址
    contract = KNOWN_CONTRACTS.get(args.contract.lower(), args.contract)

    # 获取 API Key
    api_key = args.api_key or get_api_key()
    if not api_key:
        print("Error: Etherscan API Key is required.", file=sys.stderr)
        print("Set: export ETHERSCAN_API_KEY='your_key'", file=sys.stderr)
        sys.exit(1)

    # 查询
    try:
        result = find_recent_users(
            args.chain,
            contract,
            api_key,
            args.method,
            args.count,
            unique=not args.all
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
