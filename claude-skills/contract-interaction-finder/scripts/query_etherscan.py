#!/usr/bin/env python3
"""
通过 Etherscan API 查询合约交互地址
支持多链：ETH, BSC, Polygon, Arbitrum, Optimism, Base 等
"""

import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional, List, Dict, Set


# Etherscan API V2 统一端点
ETHERSCAN_V2_ENDPOINT = "https://api.etherscan.io/v2/api"

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


def get_api_key(chain: str) -> str:
    """获取对应链的 API Key"""
    # 优先使用链特定的 key，否则使用通用 key
    chain_key = os.environ.get(f"{chain.upper()}_API_KEY")
    if chain_key:
        return chain_key
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
            if data.get("status") == "0":
                msg = data.get("message", "")
                result = data.get("result", "")
                if "No transactions found" not in msg and "No records found" not in msg:
                    if isinstance(result, str):
                        if "rate limit" in result.lower():
                            raise Exception("Rate limit exceeded. Please wait and try again.")
                        if "invalid api" in result.lower() or "missing" in result.lower():
                            raise Exception(f"API Error: {result}")
            return data
    except (HTTPError, URLError) as e:
        raise Exception(f"Request failed: {e}")


def get_contract_transactions(
    chain: str,
    contract: str,
    api_key: str,
    start_block: int = 0,
    end_block: int = 99999999
) -> List[dict]:
    """
    获取合约的所有交易
    """
    params = {
        "module": "account",
        "action": "txlist",
        "address": contract,
        "startblock": start_block,
        "endblock": end_block,
        "page": 1,
        "offset": 1000,
        "sort": "desc"
    }

    result = api_call(chain, params, api_key)
    return result.get("result", []) if isinstance(result.get("result"), list) else []


def get_token_transfers(
    chain: str,
    contract: str,
    api_key: str,
    start_block: int = 0,
    end_block: int = 99999999
) -> List[dict]:
    """
    获取合约的 Token 转账记录
    """
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract,
        "startblock": start_block,
        "endblock": end_block,
        "page": 1,
        "offset": 1000,
        "sort": "desc"
    }

    result = api_call(chain, params, api_key)
    return result.get("result", []) if isinstance(result.get("result"), list) else []


def find_interacting_addresses(
    chain: str,
    contract: str,
    api_key: str,
    watch_addresses: Optional[Set[str]] = None
) -> Dict:
    """
    查找与合约交互过的地址

    Args:
        chain: 区块链网络
        contract: 合约地址
        api_key: Etherscan API Key
        watch_addresses: 可选，要筛选的观测地址集合（小写）

    Returns:
        交互地址统计信息
    """
    all_addresses = {}

    # 获取普通交易
    print(f"Fetching transactions for {contract}...", file=sys.stderr)
    txs = get_contract_transactions(chain, contract, api_key)

    for tx in txs:
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()

        for addr in [from_addr, to_addr]:
            if addr and addr != contract.lower():
                # 如果指定了观测地址，只统计匹配的
                if watch_addresses and addr not in watch_addresses:
                    continue

                if addr not in all_addresses:
                    all_addresses[addr] = {
                        "address": addr,
                        "tx_count": 0,
                        "first_tx": None,
                        "last_tx": None,
                        "tx_hashes": []
                    }

                all_addresses[addr]["tx_count"] += 1
                timestamp = tx.get("timeStamp", "")

                if all_addresses[addr]["first_tx"] is None or timestamp < all_addresses[addr]["first_tx"]:
                    all_addresses[addr]["first_tx"] = timestamp
                if all_addresses[addr]["last_tx"] is None or timestamp > all_addresses[addr]["last_tx"]:
                    all_addresses[addr]["last_tx"] = timestamp

                if len(all_addresses[addr]["tx_hashes"]) < 5:
                    all_addresses[addr]["tx_hashes"].append(tx.get("hash", ""))

    # Rate limit: 等待一下再请求
    time.sleep(0.25)

    # 获取 Token 转账
    print(f"Fetching token transfers for {contract}...", file=sys.stderr)
    transfers = get_token_transfers(chain, contract, api_key)

    for tx in transfers:
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()

        for addr in [from_addr, to_addr]:
            if addr and addr != contract.lower():
                if watch_addresses and addr not in watch_addresses:
                    continue

                if addr not in all_addresses:
                    all_addresses[addr] = {
                        "address": addr,
                        "tx_count": 0,
                        "first_tx": None,
                        "last_tx": None,
                        "tx_hashes": []
                    }

                all_addresses[addr]["tx_count"] += 1
                timestamp = tx.get("timeStamp", "")

                if all_addresses[addr]["first_tx"] is None or timestamp < all_addresses[addr]["first_tx"]:
                    all_addresses[addr]["first_tx"] = timestamp
                if all_addresses[addr]["last_tx"] is None or timestamp > all_addresses[addr]["last_tx"]:
                    all_addresses[addr]["last_tx"] = timestamp

    # 转换时间戳为可读格式
    for addr_info in all_addresses.values():
        if addr_info["first_tx"]:
            try:
                addr_info["first_tx"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(int(addr_info["first_tx"]))
                )
            except (ValueError, TypeError):
                pass
        if addr_info["last_tx"]:
            try:
                addr_info["last_tx"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(int(addr_info["last_tx"]))
                )
            except (ValueError, TypeError):
                pass

    # 按交易数排序
    sorted_addresses = sorted(
        all_addresses.values(),
        key=lambda x: x["tx_count"],
        reverse=True
    )

    return {
        "contract": contract,
        "chain": chain,
        "total_unique_addresses": len(sorted_addresses),
        "interacted_addresses": sorted_addresses[:100]  # 只返回前 100 个
    }


def main():
    parser = argparse.ArgumentParser(
        description="通过 Etherscan API 查询合约交互地址"
    )
    parser.add_argument(
        "--chain",
        required=True,
        choices=list(CHAIN_IDS.keys()),
        help="区块链网络"
    )
    parser.add_argument(
        "--contract",
        required=True,
        help="合约地址"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Etherscan API Key (或设置 ETHERSCAN_API_KEY 环境变量)"
    )
    parser.add_argument(
        "--watch-list",
        help="观测地址列表文件 (每行一个地址)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="显示前 N 个地址 (默认: 20)"
    )

    args = parser.parse_args()

    # 获取 API Key
    api_key = args.api_key or get_api_key(args.chain)
    if not api_key:
        print("Error: Etherscan API Key is required.", file=sys.stderr)
        print("Get your free API key at: https://etherscan.io/myapikey", file=sys.stderr)
        print("Then set: export ETHERSCAN_API_KEY='your_key'", file=sys.stderr)
        sys.exit(1)

    # 加载观测地址
    watch_addresses = None
    if args.watch_list:
        try:
            with open(args.watch_list) as f:
                watch_addresses = set(
                    line.strip().lower()
                    for line in f
                    if line.strip() and line.strip().startswith("0x")
                )
            print(f"Loaded {len(watch_addresses)} watch addresses", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to load watch list: {e}", file=sys.stderr)

    # 查询
    try:
        result = find_interacting_addresses(
            args.chain,
            args.contract,
            api_key,
            watch_addresses
        )

        # 限制输出数量
        result["interacted_addresses"] = result["interacted_addresses"][:args.top]

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
