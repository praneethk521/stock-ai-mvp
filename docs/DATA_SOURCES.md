# Data Sources

## Recommended Provider Priority
1. Polygon or Finnhub for production-grade price/fundamental/news integrations
2. Alpha Vantage for market data, technical indicators, and news sentiment
3. Tiingo/IEX-style providers as additional adapters
4. Yahoo Finance-compatible libraries only for local/dev experimentation, not primary production dependency

## Notes
- Polygon provides real-time and historical stock market data APIs.
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

## Compliance
Use licensed APIs where possible. Scraping should be opt-in, compliant with site terms, and respectful of robots.txt.
