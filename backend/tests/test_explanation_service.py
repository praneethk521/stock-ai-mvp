from app.services.explanation_service import ExplanationService
from app.services.recommendation_engine import RecommendationEngine


def test_fallback_explanation_includes_signals_and_risk_notes():
    snapshot = {
        'change_percent': 3,
        'volume_change_percent': 60,
        'rsi': 74,
        'macd_signal': 'bullish',
        'moving_average_signal': 'bullish',
        'market_cap': 100_000_000_000,
        'volatility': 0.45,
    }
    recommendation = RecommendationEngine().generate('NVDA', snapshot, sentiment_score=0.5)

    explanation = ExplanationService().generate('NVDA', recommendation, snapshot, sentiment_score=0.5)

    assert explanation.ticker == 'NVDA'
    assert explanation.provider == 'rules-fallback'
    assert explanation.model_version == 'explanation-fallback-v1'
    assert explanation.signal_summary
    assert any('RSI is overbought' in note for note in explanation.risk_notes)
    assert explanation.disclaimer
