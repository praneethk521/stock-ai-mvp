# Data Sources

## Production Provider Priority
1. Polygon as the primary production provider for market data, snapshots, indicators, and ticker news
2. Secondary provider later for redundancy and provider-diff checks
3. Alpha Vantage/Finnhub only as fallback or enrichment adapters
4. Yahoo Finance-compatible libraries only for local/dev experimentation, not primary production dependency

## Notes
- Polygon provides stock snapshots, top market movers, technical indicators, aggregates, reference data, and ticker news with sentiment insights.
- Finnhub lists real-time market data, company fundamentals, company news, and sentiment-related APIs.
- Alpha Vantage provides market data APIs and a news/sentiment endpoint; it also advertises an official MCP server.

## Provider Contract
Every provider should implement:
- latest quote/snapshot
- historical candles
- company fundamentals
- company news
- market movers, if supported
- rate-limit metadata

## Polygon Integration Status
- [x] Configurable Polygon client
- [x] Polygon market snapshot adapter for tracked mega-cap tickers
- [x] Polygon ticker reference lookup for market cap
- [x] Polygon news adapter using `/v2/reference/news`
- [x] Polygon market status health check using `/v1/marketstatus/now`
- [x] In-process provider response caching
- [x] Retry/backoff for transient Polygon errors
- [x] Polygon RSI, MACD, and SMA indicator enrichment
- [ ] Polygon top market movers endpoint integration
- [ ] Polygon aggregates/candles for custom technical calculations
- [ ] Redis-backed provider cache
- [ ] Structured provider request logging

## Compliance
Use licensed APIs where possible. Scraping should be opt-in, compliant with site terms, and respectful of robots.txt.
