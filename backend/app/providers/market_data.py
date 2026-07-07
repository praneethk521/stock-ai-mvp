from abc import ABC, abstractmethod
from app.schemas.market import MarketMover


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_market_overview(self) -> dict: ...

    @abstractmethod
    async def get_large_cap_movers(self, min_market_cap: float = 50_000_000_000) -> list[MarketMover]: ...

    @abstractmethod
    async def get_top_market_movers(self, direction: str = 'gainers', limit: int = 10) -> list[MarketMover]: ...

    @abstractmethod
    async def get_ticker_snapshot(self, ticker: str) -> dict: ...


MEGA_CAP_UNIVERSE = [
    MarketMover(ticker='NVDA', company_name='NVIDIA Corp', price=200.09, change_percent=2.63, volume=82_000_000, market_cap=4_846_000_000_000),
    MarketMover(ticker='GOOG', company_name='Alphabet Inc', price=353.33, change_percent=0.58, volume=21_000_000, market_cap=4_311_000_000_000),
    MarketMover(ticker='AAPL', company_name='Apple Inc', price=289.36, change_percent=2.70, volume=51_000_000, market_cap=4_249_000_000_000),
    MarketMover(ticker='MSFT', company_name='Microsoft Corp', price=510.10, change_percent=1.20, volume=22_000_000, market_cap=3_800_000_000_000),
    MarketMover(ticker='AMZN', company_name='Amazon.com Inc', price=246.90, change_percent=-1.84, volume=38_000_000, market_cap=2_650_000_000_000),
    MarketMover(ticker='META', company_name='Meta Platforms Inc', price=712.42, change_percent=-2.21, volume=19_000_000, market_cap=1_800_000_000_000),
    MarketMover(ticker='AVGO', company_name='Broadcom Inc', price=384.50, change_percent=3.86, volume=31_000_000, market_cap=1_790_000_000_000),
    MarketMover(ticker='TSM', company_name='Taiwan Semiconductor Manufacturing Co', price=306.72, change_percent=-3.14, volume=14_000_000, market_cap=1_590_000_000_000),
    MarketMover(ticker='TSLA', company_name='Tesla Inc', price=498.22, change_percent=4.42, volume=76_000_000, market_cap=1_580_000_000_000),
    MarketMover(ticker='BRK.B', company_name='Berkshire Hathaway Inc', price=548.18, change_percent=0.36, volume=4_800_000, market_cap=1_074_000_000_000),
]


class MockMarketDataProvider(MarketDataProvider):
    async def get_market_overview(self) -> dict:
        return {
            'indices': [
                {'symbol': 'SPY', 'change_percent': 0.42},
                {'symbol': 'QQQ', 'change_percent': 0.76},
                {'symbol': 'DIA', 'change_percent': 0.18},
            ],
            'tracked_tickers': [item.ticker for item in MEGA_CAP_UNIVERSE],
            'disclaimer': 'Mock data for local development only.'
        }

    async def get_large_cap_movers(self, min_market_cap: float = 50_000_000_000) -> list[MarketMover]:
        filtered = [item for item in MEGA_CAP_UNIVERSE if item.market_cap >= min_market_cap]
        return sorted(filtered, key=lambda item: abs(item.change_percent), reverse=True)

    async def get_top_market_movers(self, direction: str = 'gainers', limit: int = 10) -> list[MarketMover]:
        reverse = direction == 'gainers'
        return sorted(MEGA_CAP_UNIVERSE, key=lambda item: item.change_percent, reverse=reverse)[:limit]

    async def get_ticker_snapshot(self, ticker: str) -> dict:
        symbol = ticker.upper()
        mover = next((item for item in MEGA_CAP_UNIVERSE if item.ticker == symbol), None)
        market_cap = mover.market_cap if mover else 125_000_000_000
        price = mover.price if mover else 250.0
        change_percent = mover.change_percent if mover else 1.7
        return {
            'ticker': symbol,
            'price': price,
            'change_percent': change_percent,
            'volume_change_percent': 45.0,
            'market_cap': market_cap,
            'rsi': 61.0,
            'macd_signal': 'bullish',
            'moving_average_signal': 'bullish',
            'volatility': 0.28,
        }
