---
name: contract-interaction-finder
description: 快速搜索与指定合约地址交互过的观测地址。当用户提供合约地址并要求查找交互地址、分析合约交互、搜索与合约有关联的地址、查找特定操作的最近用户时触发。支持多链（EVM、Solana），使用 Etherscan API 和 Helius API 获取交互记录。支持 ABI 解码，可解析 Aave、Compound、Lido、Uniswap 等协议的交易参数。
---

# Contract Interaction Finder

查找与指定合约地址交互过的地址，支持按操作类型过滤、时间排序、ABI 参数解码。

## 快速使用

### EVM 链（Ethereum/BSC/Polygon 等）

```bash
# Lido 质押 - 最近 5 个地址
python scripts/query_contract_users.py --contract lido --method submit --count 5

# Aave V3 借款 - 最近 5 个地址
python scripts/query_contract_users.py --contract aave_v3 --method borrow --count 5

# Compound V2 还款 - 最近 5 个地址
python scripts/query_contract_users.py --contract cusdc --method repayBorrow --count 5
```

### Solana

```bash
# Kamino SOL 池 repay - 最近 5 个地址
python scripts/query_solana.py --program kamino-sol --type repay --count 5

# Kamino USDC 池 borrow - 最近 5 个地址
python scripts/query_solana.py --program kamino-usdc --type borrow --count 5

# Jupiter 交换 - 最近 5 个地址
python scripts/query_solana.py --program jupiter --type swap --count 5
```

## 脚本

### query_contract_users.py（EVM 链）

查询 EVM 链合约的最近用户，支持 ABI 解码：

```bash
python scripts/query_contract_users.py \
  --contract aave_v3 \
  --method borrow \
  --count 5
```

参数：
- `--contract`: 合约地址或快捷名称
- `--method`: 方法名过滤（可选）
- `--count`: 返回数量（默认 5）
- `--chain`: 区块链（默认 ethereum）

#### EVM 快捷合约名称

**质押协议**

| 名称 | 合约地址 | 说明 |
|------|----------|------|
| `lido` | 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 | Lido stETH |
| `lido_withdrawal` | 0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1 | Lido Withdrawal |
| `everstake` | 0xd523794c879d9ec028960a231f866758e405be34 | Everstake |

**Aave 借贷**

| 名称 | 合约地址 | 说明 |
|------|----------|------|
| `aave_v3` | 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 | Aave V3 Pool |
| `aave_v2` | 0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9 | Aave V2 Pool |

**Compound 借贷**

| 名称 | 合约地址 | 说明 |
|------|----------|------|
| `compound_v3_usdc` | 0xc3d688B66703497DAA19211EEdff47f25384cdc3 | Compound V3 USDC |
| `compound_v3_weth` | 0xA17581A9E3356d9A858b789D68B4d866e593aE94 | Compound V3 WETH |
| `cusdc` | 0x39AA39c021dfbaE8faC545936693aC917d5E7563 | Compound V2 cUSDC |
| `ceth` | 0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5 | Compound V2 cETH |
| `cdai` | 0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643 | Compound V2 cDAI |

**代币**

| 名称 | 合约地址 |
|------|----------|
| `usdt` | 0xdAC17F958D2ee523a2206206994597C13D831ec7 |
| `usdc` | 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 |
| `weth` | 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 |
| `dai` | 0x6B175474E89094C44Da98b954EescdedDAC495271d0F |
| `wbtc` | 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599 |

**DEX**

| 名称 | 合约地址 |
|------|----------|
| `uniswap_v3_router` | 0xE592427A0AEce92De3Edee1F18E0157C05861564 |
| `uniswap_v2_router` | 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D |

#### EVM 方法过滤

**通用方法**

| 方法 | 说明 |
|------|------|
| `transfer` | ERC20 转账 |
| `approve` | ERC20 授权 |
| `deposit` | 存款 |
| `withdraw` | 提款 |

**Lido**

| 方法 | 说明 |
|------|------|
| `submit` | 质押 ETH |
| `requestWithdrawals` | 请求提款 |

**Aave V3**

| 方法 | 说明 | 解码参数 |
|------|------|----------|
| `supply` | 存款 | asset, amount, onBehalfOf |
| `aave_withdraw` | 提款 | asset, amount, to |
| `borrow` | 借款 | asset, amount, interestRateMode, onBehalfOf |
| `repay` | 还款 | asset, amount, interestRateMode, onBehalfOf |
| `liquidate` | 清算 | collateralAsset, debtAsset, user, debtToCover |
| `flashloan` | 闪电贷 | receiverAddress, assets, amounts |

**Compound V2**

| 方法 | 说明 | 解码参数 |
|------|------|----------|
| `mint` | 存款 | mintAmount |
| `redeem` | 赎回 cToken | redeemTokens |
| `compound_borrow` | 借款 | borrowAmount |
| `repayBorrow` | 还款 | repayAmount |
| `liquidateBorrow` | 清算 | borrower, repayAmount, cTokenCollateral |

**Compound V3**

| 方法 | 说明 | 解码参数 |
|------|------|----------|
| `compound_supply` | 存款 | asset, amount |
| `compound_withdraw` | 提款 | asset, amount |

---

### query_solana.py（Solana）

查询 Solana 程序的最近用户：

```bash
python scripts/query_solana.py \
  --program kamino-usdc \
  --type borrow \
  --count 5
```

参数：
- `--program`: 程序地址或快捷名称
- `--type`: 交易类型过滤
- `--count`: 返回数量（默认 5）

#### Solana 快捷程序名称

**质押协议**

| 名称 | 程序地址 | 说明 |
|------|----------|------|
| `marinade` | MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD | Marinade Finance |
| `jito` | Jito4APyf642JPZPx3hGc6WWJ8zPKtRbRs4P815Awbb | Jito 质押 |
| `sanctum` | SP12tWFxD9oJsVWNavTTBZvMbA6gkAmxtVgxdqvyvhY | Sanctum |
| `blaze` | BLZEEuZUBVqFhj8adcCFPJvPVCiCyVmh3hkJMrU8KuJA | BlazeStake |

**DEX**

| 名称 | 程序地址 | 说明 |
|------|----------|------|
| `raydium` | 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 | Raydium AMM |
| `orca` | whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc | Orca Whirlpool |
| `jupiter` | JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4 | Jupiter 聚合器 |

**借贷协议**

| 名称 | 程序地址 | 说明 |
|------|----------|------|
| `solend` | So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo | Solend |
| `marginfi` | MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA | MarginFi |
| `kamino` | d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q | Kamino 主程序 |

**Kamino 代币池**（使用 `kamino-<token>` 格式）：

| 名称 | 地址 |
|------|------|
| `kamino-sol` | d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q |
| `kamino-usdc` | D6q6wuQSrifJKZYpR1M8R4YawnLDtDsMmWM1NbBmgJ59 |
| `kamino-usdt` | H3t6qZ1JkguCNTi9uzVKqQ7dvt2cum4XiXWom6Gn5e5S |
| `kamino-jitosol` | EVbyPKrHG6WBfm4dLxLMJpUDY43cCAcHSpV3KYjKsktW |
| `kamino-msol` | FBSyPnxtHKLBZ4UeeUyAnbtFuAmTHLtso9YtsqRDRWpM |
| `kamino-bsol` | H9vmCVd77N1HZa36eBn3UnftYmg4vQzPfm1RxabHAMER |

更多 Kamino 池见脚本 KNOWN_PROGRAMS。

#### Solana 交易类型过滤

| 类型 | 说明 |
|------|------|
| `stake` | 质押 |
| `unstake` | 解质押 |
| `swap` | 交换 |
| `transfer` | 转账 |
| `borrow` | 借款 |
| `repay` | 还款 |
| `deposit` | 存款 |
| `withdraw` | 提款 |
| `liquidate` | 清算 |

---

## ABI 解码

EVM 脚本支持自动解码交易参数，返回人类可读的数据：

```json
{
  "address": "0x94b1...",
  "method": "borrow",
  "decoded_params": {
    "asset": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "amount": 15399369,
    "amount_formatted": 15.399369,
    "interestRateMode": 2,
    "onBehalfOf": "0x94b1..."
  }
}
```

支持的代币精度自动识别：
- USDT/USDC: 6 位
- WETH/stETH/wstETH/DAI: 18 位
- WBTC: 8 位
- Compound cTokens: 自动使用 underlying 精度

---

## 环境变量

```bash
# EVM 链（必需）
export ETHERSCAN_API_KEY="your_key"  # https://etherscan.io/myapikey

# Solana（必需）
export HELIUS_API_KEY="your_key"     # https://dev.helius.xyz/
```

## 支持的链

### EVM 链

| 链 | 标识符 | Chain ID |
|----|--------|----------|
| Ethereum | `ethereum` | 1 |
| BSC | `bsc` | 56 |
| Polygon | `polygon` | 137 |
| Arbitrum | `arbitrum` | 42161 |
| Optimism | `optimism` | 10 |
| Base | `base` | 8453 |
| Avalanche | `avalanche` | 43114 |
| Fantom | `fantom` | 250 |

### Solana

使用 Helius API，支持 Solana Mainnet。

## 输出格式

### EVM (query_contract_users.py)

```json
{
  "contract": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
  "chain": "ethereum",
  "method_filter": "borrow",
  "users": [
    {
      "address": "0x94b1...",
      "tx_hash": "0xa901...",
      "time": "2024-01-17 23:52:11",
      "value_eth": 0.0,
      "method": "borrow",
      "block": 24255477,
      "decoded_params": {
        "asset": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "amount": 15399369,
        "amount_formatted": 15.399369,
        "interestRateMode": 2,
        "onBehalfOf": "0x94b1..."
      }
    }
  ]
}
```

### Solana (query_solana.py)

```json
{
  "program": "d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q",
  "chain": "solana",
  "type_filter": "borrow",
  "users": [
    {
      "address": "2eXZW...",
      "signature": "F3cLd...",
      "time": "2024-01-17 23:16:41",
      "type": "BORROW",
      "amount_sol": 0,
      "description": "Instruction: RefreshPriceList"
    }
  ]
}
```

## 使用示例

```
用户: 帮我查找最近在 Lido 质押的 5 个地址
用户: 查询 Aave V3 最近借款的 3 个地址
用户: 找出 Compound cUSDC 最近还款的用户
用户: 查询 Kamino USDC 池最近 borrow 的 2 个地址
用户: 找出 Jupiter 最近 swap 的 5 个地址
```
