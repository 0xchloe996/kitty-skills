# Chain Configuration

## RPC Endpoints

配置 `RPC_ENDPOINTS` 环境变量为 JSON 格式：

```json
{
  "ethereum": "https://eth-mainnet.g.alchemy.com/v2/<API_KEY>",
  "bsc": "https://bsc-dataseed.binance.org",
  "polygon": "https://polygon-rpc.com",
  "arbitrum": "https://arb1.arbitrum.io/rpc",
  "optimism": "https://mainnet.optimism.io",
  "avalanche": "https://api.avax.network/ext/bc/C/rpc",
  "base": "https://mainnet.base.org",
  "solana": "https://api.mainnet-beta.solana.com",
  "tron": "https://api.trongrid.io"
}
```

## 链标识符

| Chain | 标识符 | 地址格式 |
|-------|--------|----------|
| Ethereum | `ethereum` | 0x... (40 hex) |
| BSC | `bsc` | 0x... (40 hex) |
| Polygon | `polygon` | 0x... (40 hex) |
| Arbitrum | `arbitrum` | 0x... (40 hex) |
| Optimism | `optimism` | 0x... (40 hex) |
| Avalanche C-Chain | `avalanche` | 0x... (40 hex) |
| Base | `base` | 0x... (40 hex) |
| Solana | `solana` | Base58 (32-44 chars) |
| Tron | `tron` | T... (34 chars) |
| Bitcoin | `bitcoin` | bc1.../1.../3... |

## 查询方法

### EVM 链

使用 `eth_getLogs` 查询与合约相关的事件：

```python
logs = web3.eth.get_logs({
    "address": contract_address,
    "fromBlock": start_block,
    "toBlock": "latest"
})
```

### Solana

使用 `getSignaturesForAddress` 查询交易签名，再用 `getTransaction` 获取详情。

### Tron

使用 TronGrid API 的 `/v1/accounts/{address}/transactions` 端点。

### Bitcoin

使用区块浏览器 API（如 Blockstream）查询地址交易。

## 推荐 RPC 服务商

| 服务商 | 支持链 | 免费额度 |
|--------|--------|----------|
| Alchemy | EVM | 300M CU/month |
| Infura | EVM | 100K req/day |
| QuickNode | 多链 | 按量计费 |
| Helius | Solana | 500K req/month |
| TronGrid | Tron | 10K req/day |
