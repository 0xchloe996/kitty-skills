#!/usr/bin/env python3
"""
通过 RPC 查询地址与合约的交互记录
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional, Union, List
from datetime import datetime


def rpc_call(endpoint: str, method: str, params: list) -> dict:
    """执行 JSON-RPC 调用"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }

    req = Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            if "error" in result:
                raise Exception(f"RPC Error: {result['error']}")
            return result.get("result")
    except (HTTPError, URLError) as e:
        raise Exception(f"Request failed: {e}")


def get_block_number(endpoint: str) -> int:
    """获取当前区块高度"""
    result = rpc_call(endpoint, "eth_blockNumber", [])
    return int(result, 16)


def get_logs_for_address(
    endpoint: str,
    contract: str,
    address: str,
    from_block: int,
    to_block: Union[int, str] = "latest"
) -> List[dict]:
    """
    获取特定地址与合约的交互日志
    通过查询合约的 Transfer 等事件，过滤出与目标地址相关的
    """
    # 将地址补齐为 topic 格式 (32 bytes)
    address_topic = "0x" + address.lower().replace("0x", "").zfill(64)

    logs = []

    # 查询 from 为该地址的交易
    try:
        from_logs = rpc_call(endpoint, "eth_getLogs", [{
            "address": contract,
            "fromBlock": hex(from_block),
            "toBlock": to_block if isinstance(to_block, str) else hex(to_block),
            "topics": [None, address_topic]  # topic[1] = from address
        }])
        logs.extend(from_logs or [])
    except Exception:
        pass

    # 查询 to 为该地址的交易
    try:
        to_logs = rpc_call(endpoint, "eth_getLogs", [{
            "address": contract,
            "fromBlock": hex(from_block),
            "toBlock": to_block if isinstance(to_block, str) else hex(to_block),
            "topics": [None, None, address_topic]  # topic[2] = to address
        }])
        logs.extend(to_logs or [])
    except Exception:
        pass

    return logs


def get_transaction_count(endpoint: str, address: str, contract: str) -> dict:
    """
    获取地址与合约的交互统计
    使用 eth_getLogs 查询所有相关事件
    """
    current_block = get_block_number(endpoint)

    # 查询最近 100 万个区块（约 4 个月的 ETH 数据）
    from_block = max(0, current_block - 1000000)

    logs = get_logs_for_address(endpoint, contract, address, from_block)

    if not logs:
        return None

    # 提取交易信息
    tx_hashes = list(set(log.get("transactionHash") for log in logs))
    blocks = [int(log.get("blockNumber"), 16) for log in logs]

    return {
        "tx_count": len(tx_hashes),
        "first_block": min(blocks),
        "last_block": max(blocks),
        "log_count": len(logs)
    }


def query_interactions(
    endpoint: str,
    contract: str,
    addresses: List[str],
    labels: Optional[dict] = None
) -> List[dict]:
    """
    批量查询多个地址与合约的交互
    """
    results = []
    labels = labels or {}

    for addr in addresses:
        try:
            stats = get_transaction_count(endpoint, addr, contract)
            if stats:
                results.append({
                    "address": addr,
                    "label": labels.get(addr, ""),
                    "tx_count": stats["tx_count"],
                    "first_block": stats["first_block"],
                    "last_block": stats["last_block"]
                })
        except Exception as e:
            print(f"Warning: Failed to query {addr}: {e}", file=sys.stderr)

    return results


def get_rpc_endpoint(chain: str) -> str:
    """获取链对应的 RPC 端点"""
    # 从环境变量读取配置
    endpoints_json = os.environ.get("RPC_ENDPOINTS", "{}")
    try:
        endpoints = json.loads(endpoints_json)
    except json.JSONDecodeError:
        endpoints = {}

    # 默认公共端点
    defaults = {
        "ethereum": "https://eth.llamarpc.com",
        "bsc": "https://bsc-dataseed.binance.org",
        "polygon": "https://polygon-rpc.com",
        "arbitrum": "https://arb1.arbitrum.io/rpc",
        "optimism": "https://mainnet.optimism.io",
        "avalanche": "https://api.avax.network/ext/bc/C/rpc",
        "base": "https://mainnet.base.org"
    }

    return endpoints.get(chain) or defaults.get(chain)


def main():
    parser = argparse.ArgumentParser(
        description="查询地址与合约的链上交互记录"
    )
    parser.add_argument(
        "--chain",
        required=True,
        help="区块链网络 (ethereum, bsc, polygon, etc.)"
    )
    parser.add_argument(
        "--contract",
        required=True,
        help="合约地址"
    )
    parser.add_argument(
        "--addresses",
        required=True,
        help="要查询的地址列表，逗号分隔"
    )
    parser.add_argument(
        "--labels",
        help="地址标签 JSON 文件路径"
    )
    parser.add_argument(
        "--rpc",
        help="自定义 RPC 端点 (覆盖默认配置)"
    )

    args = parser.parse_args()

    # 获取 RPC 端点
    endpoint = args.rpc or get_rpc_endpoint(args.chain)
    if not endpoint:
        print(f"Error: 未找到 {args.chain} 的 RPC 端点配置", file=sys.stderr)
        sys.exit(1)

    # 解析地址列表
    addresses = [a.strip() for a in args.addresses.split(",") if a.strip()]

    # 加载标签
    labels = {}
    if args.labels:
        try:
            with open(args.labels) as f:
                label_data = json.load(f)
                labels = {item["address"]: item.get("label", "") for item in label_data}
        except Exception as e:
            print(f"Warning: Failed to load labels: {e}", file=sys.stderr)

    # 查询交互
    results = query_interactions(endpoint, args.contract, addresses, labels)

    # 输出结果
    output = {
        "contract": args.contract,
        "chain": args.chain,
        "interacted_addresses": results,
        "total_matches": len(results),
        "total_queried": len(addresses)
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
