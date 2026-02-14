#!/usr/bin/env python3
"""
从 Arkham Intelligence API 获取观测地址列表
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ARKHAM_API_BASE = "https://api.arkhamintelligence.com"


def get_watched_addresses(api_key: str, limit: int = 100) -> list[dict]:
    """
    获取 Arkham 观测地址列表

    Returns:
        [{"address": "0x...", "label": "...", "chain": "..."}, ...]
    """
    url = f"{ARKHAM_API_BASE}/intelligence/address?limit={limit}"

    headers = {
        "API-Key": api_key,
        "Accept": "application/json"
    }

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            addresses = []
            for item in data.get("addresses", []):
                addresses.append({
                    "address": item.get("address"),
                    "label": item.get("arkhamLabel", {}).get("name", "Unknown"),
                    "chain": item.get("chain", "ethereum"),
                    "entity": item.get("arkhamEntity", {}).get("name", "")
                })

            return addresses

    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def get_portfolio_addresses(api_key: str, entity_id: str) -> list[dict]:
    """
    获取特定实体的所有地址
    """
    url = f"{ARKHAM_API_BASE}/intelligence/entity/{entity_id}"

    headers = {
        "API-Key": api_key,
        "Accept": "application/json"
    }

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            addresses = []
            for addr in data.get("addresses", []):
                addresses.append({
                    "address": addr.get("address"),
                    "label": addr.get("arkhamLabel", {}).get("name", ""),
                    "chain": addr.get("chain", "ethereum")
                })

            return addresses

    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="获取 Arkham 观测地址列表"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("ARKHAM_API_KEY"),
        help="Arkham API Key (或设置 ARKHAM_API_KEY 环境变量)"
    )
    parser.add_argument(
        "--entity",
        help="获取特定实体的地址（实体 ID）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="返回地址数量限制 (默认: 100)"
    )
    parser.add_argument(
        "--chain",
        help="按链过滤 (ethereum, bsc, polygon, etc.)"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: 需要提供 --api-key 或设置 ARKHAM_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)

    if args.entity:
        addresses = get_portfolio_addresses(args.api_key, args.entity)
    else:
        addresses = get_watched_addresses(args.api_key, args.limit)

    if args.chain:
        addresses = [a for a in addresses if a["chain"] == args.chain]

    print(json.dumps(addresses, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
