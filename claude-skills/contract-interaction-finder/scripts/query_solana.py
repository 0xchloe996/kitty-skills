#!/usr/bin/env python3
"""
查询 Solana 合约/程序的最近交互用户
使用 Helius API 或 Solana RPC
"""

import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional, List, Dict, Set


# Helius API 端点
HELIUS_API_BASE = "https://api.helius.xyz/v0"
HELIUS_RPC_BASE = "https://mainnet.helius-rpc.com"

# 常用 Solana 程序地址
KNOWN_PROGRAMS = {
    # 质押
    "marinade": "MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD",       # Marinade Finance
    "jito": "Jito4APyf642JPZPx3hGc6WWJ8zPKtRbRs4P815Awbb",          # Jito Staking
    "sanctum": "SP12tWFxD9oJsVWNavTTBZvMbA6gkAmxtVgxdqvyvhY",       # Sanctum
    "blaze": "BLZEEuZUBVqFhj8adcCFPJvPVCiCyVmh3hkJMrU8KuJA",        # BlazeStake

    # DEX
    "raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",      # Raydium AMM
    "orca": "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",          # Orca Whirlpool
    "jupiter": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",       # Jupiter Aggregator

    # Token
    "token_program": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "token_2022": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",

    # 借贷
    "solend": "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",        # Solend
    "marginfi": "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",      # MarginFi

    # Kamino Finance - 各代币池
    "kamino": "d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q",        # Kamino 主程序
    "kamino-sol": "d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q",
    "kamino-usdc": "D6q6wuQSrifJKZYpR1M8R4YawnLDtDsMmWM1NbBmgJ59",
    "kamino-pyusd": "2gc9Dm1eB6UgVYFBUN9bWks6Kes9PbWSaPaa9DqyvEiN",
    "kamino-cbbtc": "37Jk2zkz23vkAYBT66HM2gaqJuNg2nYLsCreQAVt5MWK",
    "kamino-cash": "ApQkX32ULJUzszZDe986aobLDLMNDoGQK8tRm6oD6SsA",
    "kamino-usdg": "ESCkPWKHmgNE7Msf77n9yzqJd5kQVWWGy3o5Mgxhvavp",
    "kamino-usds": "BHUi32TrEsfN2U821G4FprKrR4hTeK4LCWtA3BFetuqA",
    "kamino-usdt": "H3t6qZ1JkguCNTi9uzVKqQ7dvt2cum4XiXWom6Gn5e5S",
    "kamino-eurc": "EGPE45iPkme8G8C1xFDNZoZeHdP3aRYtaAfAQuuwrcGZ",
    "kamino-jitosol": "EVbyPKrHG6WBfm4dLxLMJpUDY43cCAcHSpV3KYjKsktW",
    "kamino-jupsol": "DGQZWCY17gGtBUgdaFs1VreJWsodkjFxndPsskwFKGpp",
    "kamino-msol": "FBSyPnxtHKLBZ4UeeUyAnbtFuAmTHLtso9YtsqRDRWpM",
    "kamino-cgntsol": "BvafE5Sm6rLrBbVRtJ2FkCzfNJQ2TjcL8bvPZULUDYrt",
    "kamino-xbtc": "4Hyrqb9Mq7y1wkq4YoqHkPdPx3VQyFY3mxMj67naC1Cb",
    "kamino-psol": "HV9KsS5mB4b9CFhDJVKdfxWBAomYfUk5PeUsdgMQsUrB",
    "kamino-fwdsol": "8qnVHjKMcWAdkFnKvmRigj9J7UAVj2ooJ83GfeNn2DpR",
    "kamino-cdcsol": "FMbsZf4HuQ1a8a7VdmALT3S8WRfu3EocphRKPXxRsfGd",
    "kamino-dsol": "StGKGcLQoTsWzQ1tFY2bWqrdiuBhqdFE4niiAutQxQB",
    "kamino-vsol": "CHBNUPdjeo2N5QkZY2uAqv7TW5EbCTMsfvaskCBuxbom",
    "kamino-dfdvsol": "CkgQnPbuHHwSv2mNdAKH79TKSqC6jsyttK9yh4MPH6z3",
    "kamino-bsol": "H9vmCVd77N1HZa36eBn3UnftYmg4vQzPfm1RxabHAMER",
    "kamino-bonksol": "Ht9NoB1udjpRqws1sCw1j2dL7MeTDHYCDdDFkbc1Arst",
    "kamino-picosol": "2UFz8kwraHybFyKhGQRwAsE5NtNpAhWs2X5grGoS7hnQ",
    "kamino-strongsol": "A2J2CEwmwa9aTKbEfNoik6YTyNep9GtvNjU65okWYhwn",
    "kamino-lanternsol": "J5oj3VKWQNKRZx3heWZx7JZC59AEDQ9UQwqqiy63nCuf",
    "kamino-adrasol": "64AZMUHLB6NYvQSt41JTer4v8NAFDCz5sUPb7dYpCxa",
    "kamino-lainesol": "HMCXsf1jFUDbvGGhvUzCzwkKbmUhxhxz7gYZwXpTuReT",
    "kamino-bbsol": "6U9CnJYCQwHUEmf4Pq4oGVKHVvD29wZvtPbFNjYmgjaF",
    "kamino-jsol": "HD93Fq3gmVh3J7euJJ5MBw8Ph3ebeMFS699JQePN4XgN",
    "kamino-nxsol": "8gVpWfWDCtCcUX1meSphqqpyWBceLCcrs9yEXwKKjQrL",
    "kamino-hsol": "CExamod1Ai3d1N8Vh7sBjt5xbZzb2VmGMAFocf7fxCzm",
    "kamino-bnsol": "Fqjbo3L4NAyzPcy6swv1XXLm1c7tUTKWMDkjCo9mfSDq",
    "kamino-hubsol": "B5uYvxUcwX5fCB4msGU4DaHh8k6fsSkKHNboy94F9vbt",
}

# 交易类型映射
TRANSACTION_TYPES = {
    "stake": ["STAKE", "STAKE_SOL", "DEPOSIT_STAKE"],
    "unstake": ["UNSTAKE", "UNSTAKE_SOL", "WITHDRAW_STAKE"],
    "swap": ["SWAP", "TOKEN_SWAP", "ROUTE_SWAP"],
    "transfer": ["TRANSFER", "TOKEN_TRANSFER", "TRANSFER_CHECKED"],
    "nft": ["NFT_SALE", "NFT_MINT", "NFT_LISTING"],
    # 借贷操作
    "borrow": ["BORROW", "LENDING_BORROW", "BORROW_OBLIGATION_LIQUIDITY"],
    "repay": ["REPAY", "LENDING_REPAY", "REPAY_OBLIGATION_LIQUIDITY"],
    "deposit": ["DEPOSIT", "LENDING_DEPOSIT", "DEPOSIT_RESERVE_LIQUIDITY"],
    "withdraw": ["WITHDRAW", "LENDING_WITHDRAW", "WITHDRAW_RESERVE_LIQUIDITY"],
    "liquidate": ["LIQUIDATE", "LENDING_LIQUIDATE", "LIQUIDATE_OBLIGATION"],
}


def get_helius_api_key() -> str:
    """获取 Helius API Key"""
    return os.environ.get("HELIUS_API_KEY", "")


def helius_api_call(endpoint: str, api_key: str, params: Optional[Dict] = None) -> dict:
    """执行 Helius API 调用"""
    url = f"{HELIUS_API_BASE}{endpoint}?api-key={api_key}"
    if params:
        for k, v in params.items():
            url += f"&{k}={v}"

    req = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        if e.code == 429:
            raise Exception("Rate limit exceeded. Please wait and try again.")
        raise Exception(f"HTTP Error {e.code}: {e.reason}")
    except URLError as e:
        raise Exception(f"Request failed: {e}")


def helius_rpc_call(method: str, params: list, api_key: str) -> dict:
    """执行 Helius RPC 调用"""
    url = f"{HELIUS_RPC_BASE}/?api-key={api_key}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }

    req = Request(
        url,
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


def get_signatures_for_address(
    address: str,
    api_key: str,
    limit: int = 100
) -> List[dict]:
    """获取地址的交易签名列表"""
    result = helius_rpc_call(
        "getSignaturesForAddress",
        [address, {"limit": limit}],
        api_key
    )
    return result or []


def get_parsed_transactions(
    signatures: List[str],
    api_key: str
) -> List[dict]:
    """获取解析后的交易详情（使用 Helius Enhanced API）"""
    if not signatures:
        return []

    # 使用 Helius parseTransaction API
    url = f"https://api.helius.xyz/v0/transactions?api-key={api_key}"

    req = Request(
        url,
        data=json.dumps({"transactions": signatures}).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        # 如果 Enhanced API 失败，回退到基础解析
        if e.code == 403:
            print("Enhanced API unavailable, using basic parsing...", file=sys.stderr)
            return get_basic_transactions(signatures, api_key)
        raise Exception(f"Request failed: {e}")
    except URLError as e:
        raise Exception(f"Request failed: {e}")


def get_solscan_api_token() -> str:
    """获取 Solscan API Token"""
    return os.environ.get("SOLSCAN_API_TOKEN", "")


def get_solscan_tx_detail(signature: str, api_token: str = "") -> Optional[dict]:
    """从 Solscan 获取交易详情（包含交易类型）"""
    if not api_token:
        api_token = get_solscan_api_token()

    url = f"https://pro-api.solscan.io/v2.0/transaction/detail?tx={signature}"

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    if api_token:
        headers["token"] = api_token

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("data", {})
    except Exception:
        return None


def parse_tx_type_from_logs(logs: List[str]) -> str:
    """从交易日志解析操作类型"""
    # 借贷操作关键词
    lending_keywords = {
        "RepayObligationLiquidity": "REPAY",
        "Instruction: Repay": "REPAY",
        "BorrowObligationLiquidity": "BORROW",
        "Instruction: Borrow": "BORROW",
        "DepositReserveLiquidity": "DEPOSIT",
        "Instruction: Deposit": "DEPOSIT",
        "WithdrawReserveLiquidity": "WITHDRAW",
        "Instruction: Withdraw": "WITHDRAW",
        "Instruction: Invest": "DEPOSIT",
        "Instruction: RedeemReserveCollateral": "WITHDRAW",
        "Instruction: LiquidateObligation": "LIQUIDATE",
    }

    # 其他操作关键词
    other_keywords = {
        "Instruction: Swap": "SWAP",
        "Instruction: Transfer": "TRANSFER",
        "Instruction: Stake": "STAKE",
        "Instruction: Unstake": "UNSTAKE",
    }

    all_keywords = {**lending_keywords, **other_keywords}

    for log in logs:
        for keyword, tx_type in all_keywords.items():
            if keyword.lower() in log.lower():
                return tx_type

    return "UNKNOWN"


def get_basic_transactions(
    signatures: List[str],
    api_key: str
) -> List[dict]:
    """使用 RPC 获取交易信息，通过日志解析操作类型"""
    transactions = []

    for sig in signatures[:60]:  # 处理更多交易以支持类型过滤
        try:
            result = helius_rpc_call(
                "getTransaction",
                [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
                api_key
            )
            if result:
                # 从日志解析操作类型
                logs = result.get("meta", {}).get("logMessages", [])
                tx_type = parse_tx_type_from_logs(logs)
                description = ""

                # 提取关键日志作为描述
                for log in logs:
                    if "Instruction:" in log and "Program log" in log:
                        description = log.replace("Program log: ", "")
                        break

                # 转换为类似 Enhanced API 的格式
                tx = {
                    "signature": sig,
                    "timestamp": result.get("blockTime", 0),
                    "feePayer": result.get("transaction", {}).get("message", {}).get("accountKeys", [{}])[0].get("pubkey", ""),
                    "type": tx_type,
                    "description": description,
                    "nativeTransfers": [],
                    "tokenTransfers": [],
                    "transactionError": result.get("meta", {}).get("err")
                }

                # 解析 native transfers
                pre_balances = result.get("meta", {}).get("preBalances", [])
                post_balances = result.get("meta", {}).get("postBalances", [])
                account_keys = result.get("transaction", {}).get("message", {}).get("accountKeys", [])

                for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
                    if pre != post and i < len(account_keys):
                        tx["nativeTransfers"].append({
                            "fromUserAccount": account_keys[i].get("pubkey", "") if pre > post else "",
                            "toUserAccount": account_keys[i].get("pubkey", "") if post > pre else "",
                            "amount": abs(post - pre)
                        })

                transactions.append(tx)
            time.sleep(0.2)  # Rate limit
        except Exception:
            continue

    return transactions


def find_program_users(
    program: str,
    api_key: str,
    tx_type: Optional[str] = None,
    count: int = 5
) -> Dict:
    """
    查找与程序交互的最近用户

    Args:
        program: 程序地址
        api_key: Helius API Key
        tx_type: 交易类型过滤 (stake/unstake/swap/transfer)
        count: 返回数量
    """
    print(f"Fetching transactions for {program}...", file=sys.stderr)

    # 获取交易签名 - 过滤特定类型时需要更多样本
    fetch_count = count * 50 if tx_type else count * 10
    signatures_data = get_signatures_for_address(program, api_key, min(fetch_count, 200))

    if not signatures_data:
        return {
            "program": program,
            "chain": "solana",
            "type_filter": tx_type,
            "users": [],
            "total_found": 0
        }

    # 提取签名列表 - 过滤时需要更多样本
    max_sigs = 100 if tx_type else 50
    signatures = [s["signature"] for s in signatures_data[:max_sigs]]

    # 获取解析后的交易
    print(f"Parsing {len(signatures)} transactions...", file=sys.stderr)
    parsed_txs = get_parsed_transactions(signatures, api_key)

    users = []
    seen_addresses = set()

    for tx in parsed_txs:
        # 跳过失败的交易
        if tx.get("transactionError"):
            continue

        # 获取交易类型
        tx_type_actual = tx.get("type", "UNKNOWN")

        # 类型过滤
        if tx_type:
            type_variants = TRANSACTION_TYPES.get(tx_type.lower(), [tx_type.upper()])
            if tx_type_actual.upper() not in [t.upper() for t in type_variants]:
                continue

        # 获取 fee payer（通常是发起者）
        fee_payer = tx.get("feePayer", "")

        if not fee_payer or fee_payer in seen_addresses:
            continue

        # 跳过程序地址本身
        if fee_payer == program:
            continue

        seen_addresses.add(fee_payer)

        # 解析时间
        timestamp = tx.get("timestamp", 0)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)) if timestamp else "unknown"

        # 获取交易描述
        description = tx.get("description", "")

        # 获取涉及的金额
        native_transfers = tx.get("nativeTransfers", [])
        token_transfers = tx.get("tokenTransfers", [])

        amount_sol = 0
        for transfer in native_transfers:
            if transfer.get("fromUserAccount") == fee_payer:
                amount_sol += transfer.get("amount", 0) / 1e9

        users.append({
            "address": fee_payer,
            "signature": tx.get("signature", ""),
            "time": time_str,
            "timestamp": timestamp,
            "type": tx_type_actual,
            "amount_sol": round(amount_sol, 6),
            "description": description[:100] if description else ""
        })

        if len(users) >= count:
            break

    return {
        "program": program,
        "chain": "solana",
        "type_filter": tx_type,
        "users": users,
        "total_found": len(users)
    }


def main():
    parser = argparse.ArgumentParser(
        description="查询 Solana 程序的最近交互用户"
    )
    parser.add_argument(
        "--program",
        required=True,
        help="程序地址或快捷名称 (marinade/jito/raydium/jupiter/orca 等)"
    )
    parser.add_argument(
        "--type",
        choices=["stake", "unstake", "swap", "transfer", "nft", "borrow", "repay", "deposit", "withdraw", "liquidate"],
        help="交易类型过滤 (stake/unstake/swap/transfer/nft/borrow/repay/deposit/withdraw/liquidate)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="返回数量 (默认: 5)"
    )
    parser.add_argument(
        "--api-key",
        help="Helius API Key (或设置 HELIUS_API_KEY 环境变量)"
    )

    args = parser.parse_args()

    # 解析程序地址
    program = KNOWN_PROGRAMS.get(args.program.lower(), args.program)

    # 获取 API Key
    api_key = args.api_key or get_helius_api_key()
    if not api_key:
        print("Error: Helius API Key is required.", file=sys.stderr)
        print("Get your free API key at: https://dev.helius.xyz/", file=sys.stderr)
        print("Then set: export HELIUS_API_KEY='your_key'", file=sys.stderr)
        sys.exit(1)

    # 查询
    try:
        result = find_program_users(
            program,
            api_key,
            args.type,
            args.count
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
