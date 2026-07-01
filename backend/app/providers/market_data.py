from abc import ABC, abstractmethod
from app.schemas.market import MarketMover


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_market_overview(self) -> dict: ...

    @abstractmethod
    async def get_large_cap_movers(self, min_market_cap: float = 50_000_000_000) -> list[MarketMover]: ...

    @abstractmethod
    async def get_ticker_snapshot(self, ticker: str) -> dict: ...


class MockMarketDataProvider(MarketDataProvider):
    async def get_market_overview(self) -> dict:
        return {
            'indices': [
                {'symbol': 'SPY', 'change_percent': 0.42},
                {'symbol': 'QQQ', 'change_percent': 0.76},
                {'symbol': 'DIA', 'change_percent': 0.18},
            ],
            'disclaimer': 'Mock data for local development only.'
        }

    async def get_large_cap_movers(self, min_market_cap: float = 50_000_000_000) -> list[MarketMover]:
        return [
            MarketMover(ticker='NVDA', company_name='NVIDIA Corp', price=140.25, change_percent=3.4, volume=82000000, market_cap=3_400_000_000_000),
            MarketMover(ticker='MSFT', company_name='Microsoft Corp', price=510.10, change_percent=1.2, volume=22000000, market_cap=3_800_000_000_000),
            MarketMover(ticker='AAPL', company_name='Apple Inc', price=230.55, change_percent=-0.8, volume=51000000, market_cap=3_500_000_000_000),
        ]

    async def get_ticker_snapshot(self, ticker: str) -> dict:
        return {
            'ticker': ticker.upper(),
            'price': 250.0,
            'change_percent': 1.7,
            'volume_change_percent': 45.0,
            'market_cap': 125_000_000_000,
            'rsi': 61.0,
            'macd_signal': 'bullish',
            'moving_average_signal': 'bullish',
            'volatility': 0.28,
        }
