from app.services.recommendation_engine import RecommendationEngine


def test_generate_recommendation_buy_signal():
    engine = RecommendationEngine()
    rec = engine.generate('NVDA', {
        'change_percent': 3,
        'volume_change_percent': 60,
        'rsi': 62,
        'macd_signal': 'bullish',
        'moving_average_signal': 'bullish',
        'market_cap': 100_000_000_000,
        'volatility': 0.2,
    }, sentiment_score=0.7)
    assert rec.recommendation == 'BUY'
    assert rec.disclaimer
