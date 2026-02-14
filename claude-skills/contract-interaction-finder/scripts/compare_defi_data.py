#!/usr/bin/env python3
"""
OneKey vs Zerion DeFi 数据对比工具

对比 OneKey 和 Zerion 的 DeFi positions 数据是否一致。

使用方法:
    # 对比单个地址
    python compare_defi_data.py --address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

    # 指定链
    python compare_defi_data.py --address 0x... --chain arbitrum

    # 对比多个地址
    python compare_defi_data.py --addresses 0x...,0x...,0x...

    # 设置差异阈值（默认 5%）
    python compare_defi_data.py --address 0x... --threshold 0.1
"""

import argparse
import json
import os
import sys
import base64
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ========== 配置 ==========
ONEKEY_API_BASE = "https://wallet.onekeytest.com"
ZERION_API_BASE = "https://api.zerion.io/v1"

# 链 ID 映射
CHAIN_MAPPING = {
    "ethereum": {"onekey": "evm--1", "zerion": "ethereum"},
    "arbitrum": {"onekey": "evm--42161", "zerion": "arbitrum"},
    "optimism": {"onekey": "evm--10", "zerion": "optimism"},
    "polygon": {"onekey": "evm--137", "zerion": "polygon"},
    "base": {"onekey": "evm--8453", "zerion": "base"},
    "bsc": {"onekey": "evm--56", "zerion": "binance-smart-chain"},
    "avalanche": {"onekey": "evm--43114", "zerion": "avalanche"},
}

# 主要协议列表（只对比这些协议）
MAJOR_PROTOCOLS = [
    "aave", "aave-v2", "aave-v3",
    "compound", "compound-v2", "compound-v3",
    "lido", "lido-v2",
    "uniswap", "uniswap-v2", "uniswap-v3",
    "curve",
    "convex",
    "maker", "makerdao",
    "yearn",
    "balancer",
    "sushiswap",
    "pancakeswap",
    "gmx",
    "radiant",
    "pendle",
    "eigenlayer",
    "rocketpool",
    "frax",
    "stargate",
]


def get_zerion_api_key() -> str:
    """获取 Zerion API Key"""
    key = os.environ.get("ZERION_API_KEY", "zk_dev_a22e808cff87411aad3c3df2f9f9a24d")
    return key


def fetch_onekey_positions(address: str, network_ids: List[str]) -> Dict:
    """获取 OneKey DeFi positions"""
    import uuid

    url = f"{ONEKEY_API_BASE}/wallet/v1/portfolio/positions"

    # 构建请求体
    body = {
        "address": address,
        "networkIds": network_ids
    }

    # 必需的 Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Onekey-Request-ID": str(uuid.uuid4()),
        "X-Onekey-Request-Currency": "usd",
        "X-Onekey-Request-Locale": "en",
        "X-Onekey-Request-Theme": "light",
        "X-Onekey-Request-Platform": "android-apk",
        "X-Onekey-Request-Version": "5.19.0",
        "X-Onekey-Request-Build-Number": "2000000000",
        "X-Onekey-Instance-Id": "38457117-2c0d-4a23-abdc-8617155229e9",
        "x-onekey-wallet-type": "hd",
    }

    req = Request(
        url,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST"
    )

    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except (HTTPError, URLError) as e:
        raise Exception(f"OneKey API failed: {e}")


def fetch_zerion_positions(address: str, chain_ids: List[str], api_key: str) -> Dict:
    """获取 Zerion DeFi positions"""
    url = f"{ZERION_API_BASE}/wallets/{address}/positions/"

    # 构建查询参数
    params = {
        "filter[positions]": "only_complex",  # 只获取 DeFi positions
        "currency": "usd",
    }
    if chain_ids:
        params["filter[chain_ids]"] = ",".join(chain_ids)

    query = "&".join(f"{k}={v}" for k, v in params.items())
    full_url = f"{url}?{query}"

    # Basic Auth: API Key 作为用户名，密码为空
    auth = base64.b64encode(f"{api_key}:".encode()).decode()

    req = Request(
        full_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {auth}"
        }
    )

    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except (HTTPError, URLError) as e:
        raise Exception(f"Zerion API failed: {e}")


def normalize_onekey_data(data: Dict) -> Dict[str, Dict]:
    """
    标准化 OneKey 数据格式
    返回: {protocol_id: {name, total_value, positions: [...]}}
    """
    normalized = {}

    positions_data = data.get("data", {}).get("data", {}).get("positions", {})

    for network_id, positions in positions_data.items():
        for pos in positions:
            protocol = pos.get("protocol", "").lower()
            protocol_name = pos.get("protocolName", protocol)

            if protocol not in normalized:
                normalized[protocol] = {
                    "name": protocol_name,
                    "total_value": 0,
                    "positions": []
                }

            # 计算仓位总值
            pos_value = sum(
                asset.get("value", 0)
                for asset in pos.get("assets", [])
            )

            normalized[protocol]["total_value"] += pos_value
            normalized[protocol]["positions"].append({
                "chain": pos.get("chain"),
                "category": pos.get("category"),
                "value": pos_value,
                "assets": [
                    {
                        "symbol": a.get("symbol"),
                        "amount": float(a.get("amount", 0)),
                        "value": a.get("value", 0)
                    }
                    for a in pos.get("assets", [])
                ]
            })

    return normalized


def normalize_zerion_data(data: Dict) -> Dict[str, Dict]:
    """
    标准化 Zerion 数据格式
    返回: {protocol_id: {name, total_value, positions: [...]}}
    """
    normalized = {}

    positions = data.get("data", [])

    for pos in positions:
        attrs = pos.get("attributes", {})

        # 获取协议信息
        app_meta = attrs.get("application_metadata") or {}
        protocol = app_meta.get("id", "").lower() or attrs.get("protocol", "unknown")
        protocol_name = app_meta.get("name", protocol)

        if protocol not in normalized:
            normalized[protocol] = {
                "name": protocol_name,
                "total_value": 0,
                "positions": []
            }

        # 获取仓位值
        pos_value = attrs.get("value") or 0

        normalized[protocol]["total_value"] += pos_value

        # 获取资产信息
        fungible = attrs.get("fungible_info", {})
        quantity = attrs.get("quantity", {})

        normalized[protocol]["positions"].append({
            "chain": attrs.get("chain"),
            "category": attrs.get("position_type"),
            "value": pos_value,
            "assets": [{
                "symbol": fungible.get("symbol"),
                "amount": quantity.get("float", 0),
                "value": pos_value
            }]
        })

    return normalized


def compare_positions(
    onekey_data: Dict[str, Dict],
    zerion_data: Dict[str, Dict],
    threshold: float = 0.05,
    major_only: bool = True
) -> Dict:
    """
    对比两个数据源的仓位

    Args:
        onekey_data: 标准化的 OneKey 数据
        zerion_data: 标准化的 Zerion 数据
        threshold: 差异阈值（百分比，默认 5%）
        major_only: 是否只对比主要协议

    Returns:
        对比结果
    """
    results = {
        "summary": {
            "total_protocols_onekey": len(onekey_data),
            "total_protocols_zerion": len(zerion_data),
            "matched": 0,
            "mismatched": 0,
            "only_in_onekey": 0,
            "only_in_zerion": 0
        },
        "differences": [],
        "matched": [],
        "only_in_onekey": [],
        "only_in_zerion": []
    }

    all_protocols = set(onekey_data.keys()) | set(zerion_data.keys())

    for protocol in all_protocols:
        # 如果只对比主要协议，跳过非主要协议
        if major_only:
            is_major = any(major in protocol for major in MAJOR_PROTOCOLS)
            if not is_major:
                continue

        onekey_pos = onekey_data.get(protocol)
        zerion_pos = zerion_data.get(protocol)

        if onekey_pos and zerion_pos:
            # 两边都有，对比数值
            onekey_value = onekey_pos["total_value"]
            zerion_value = zerion_pos["total_value"]

            # 计算差异百分比
            if zerion_value > 0:
                diff_pct = abs(onekey_value - zerion_value) / zerion_value
            elif onekey_value > 0:
                diff_pct = 1.0  # Zerion 为 0，OneKey 有值
            else:
                diff_pct = 0  # 两边都是 0

            if diff_pct > threshold:
                results["differences"].append({
                    "protocol": protocol,
                    "name": onekey_pos["name"],
                    "onekey_value": round(onekey_value, 2),
                    "zerion_value": round(zerion_value, 2),
                    "diff_pct": round(diff_pct * 100, 2),
                    "diff_usd": round(onekey_value - zerion_value, 2)
                })
                results["summary"]["mismatched"] += 1
            else:
                results["matched"].append({
                    "protocol": protocol,
                    "name": onekey_pos["name"],
                    "value": round(onekey_value, 2)
                })
                results["summary"]["matched"] += 1

        elif onekey_pos and not zerion_pos:
            # 只在 OneKey 有
            results["only_in_onekey"].append({
                "protocol": protocol,
                "name": onekey_pos["name"],
                "value": round(onekey_pos["total_value"], 2)
            })
            results["summary"]["only_in_onekey"] += 1

        elif zerion_pos and not onekey_pos:
            # 只在 Zerion 有
            results["only_in_zerion"].append({
                "protocol": protocol,
                "name": zerion_pos["name"],
                "value": round(zerion_pos["total_value"], 2)
            })
            results["summary"]["only_in_zerion"] += 1

    return results


def format_report(results: Dict, address: str, chain: str) -> str:
    """格式化对比报告"""
    lines = []

    lines.append("\n" + "=" * 60)
    lines.append(f"  OneKey vs Zerion DeFi 数据对比报告")
    lines.append("=" * 60)
    lines.append(f"\n地址: {address}")
    lines.append(f"链: {chain}")

    summary = results["summary"]
    lines.append(f"\n--- 摘要 ---")
    lines.append(f"OneKey 协议数: {summary['total_protocols_onekey']}")
    lines.append(f"Zerion 协议数: {summary['total_protocols_zerion']}")
    lines.append(f"匹配: {summary['matched']}")
    lines.append(f"差异: {summary['mismatched']}")
    lines.append(f"仅 OneKey: {summary['only_in_onekey']}")
    lines.append(f"仅 Zerion: {summary['only_in_zerion']}")

    if results["differences"]:
        lines.append(f"\n--- 数据差异 (需关注) ---")
        for diff in sorted(results["differences"], key=lambda x: abs(x["diff_usd"]), reverse=True):
            lines.append(f"\n[{diff['name']}] ({diff['protocol']})")
            lines.append(f"  OneKey: ${diff['onekey_value']:,.2f}")
            lines.append(f"  Zerion: ${diff['zerion_value']:,.2f}")
            lines.append(f"  差异: {diff['diff_pct']}% (${diff['diff_usd']:+,.2f})")

    if results["only_in_onekey"]:
        lines.append(f"\n--- 仅在 OneKey 显示 ---")
        for item in results["only_in_onekey"]:
            lines.append(f"  {item['name']}: ${item['value']:,.2f}")

    if results["only_in_zerion"]:
        lines.append(f"\n--- 仅在 Zerion 显示 ---")
        for item in results["only_in_zerion"]:
            lines.append(f"  {item['name']}: ${item['value']:,.2f}")

    if results["matched"]:
        lines.append(f"\n--- 匹配的协议 ---")
        for item in sorted(results["matched"], key=lambda x: x["value"], reverse=True):
            lines.append(f"  {item['name']}: ${item['value']:,.2f}")

    if not results["differences"] and not results["only_in_onekey"] and not results["only_in_zerion"]:
        lines.append("\n✅ 数据一致，无明显差异！")
    else:
        lines.append(f"\n⚠️ 发现 {len(results['differences'])} 处数据差异")

    lines.append("\n" + "=" * 60 + "\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="OneKey vs Zerion DeFi 数据对比工具"
    )
    parser.add_argument("--address", help="钱包地址")
    parser.add_argument("--addresses", help="多个钱包地址，逗号分隔")
    parser.add_argument(
        "--chain",
        default="ethereum",
        choices=list(CHAIN_MAPPING.keys()),
        help="区块链 (默认: ethereum)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="差异阈值百分比 (默认: 0.05 即 5%%)"
    )
    parser.add_argument(
        "--all-protocols",
        action="store_true",
        help="对比所有协议，不只是主要协议"
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    # 获取地址列表
    addresses = []
    if args.address:
        addresses.append(args.address)
    if args.addresses:
        addresses.extend(a.strip() for a in args.addresses.split(",") if a.strip())

    if not addresses:
        print("Error: 请提供至少一个地址 (--address 或 --addresses)", file=sys.stderr)
        sys.exit(1)

    # 获取链配置
    chain_config = CHAIN_MAPPING.get(args.chain)
    if not chain_config:
        print(f"Error: 不支持的链: {args.chain}", file=sys.stderr)
        sys.exit(1)

    zerion_api_key = get_zerion_api_key()

    all_results = []

    for address in addresses:
        print(f"\n正在对比地址: {address} ({args.chain})...", file=sys.stderr)

        try:
            # 获取 OneKey 数据
            print("  获取 OneKey 数据...", file=sys.stderr)
            onekey_raw = fetch_onekey_positions(address, [chain_config["onekey"]])
            onekey_data = normalize_onekey_data(onekey_raw)

            # 获取 Zerion 数据
            print("  获取 Zerion 数据...", file=sys.stderr)
            zerion_raw = fetch_zerion_positions(address, [chain_config["zerion"]], zerion_api_key)
            zerion_data = normalize_zerion_data(zerion_raw)

            # 对比
            print("  对比数据...", file=sys.stderr)
            results = compare_positions(
                onekey_data,
                zerion_data,
                threshold=args.threshold,
                major_only=not args.all_protocols
            )

            results["address"] = address
            results["chain"] = args.chain
            all_results.append(results)

            if not args.json:
                print(format_report(results, address, args.chain))

        except Exception as e:
            print(f"Error processing {address}: {e}", file=sys.stderr)
            all_results.append({
                "address": address,
                "chain": args.chain,
                "error": str(e)
            })

    if args.json:
        print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
