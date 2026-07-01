from datetime import datetime, timezone
from app.schemas.market import Recommendation


class RecommendationEngine:
    model_version = 'rules-v1'

    def generate(self, ticker: str, snapshot: dict, sentiment_score: float) -> Recommendation:
        score = 0.0
        signals: dict[str, object] = {}

        change = float(snapshot.get('change_percent', 0))
        volume_change = float(snapshot.get('volume_change_percent', 0))
        rsi = float(snapshot.get('rsi', 50))
        volatility = float(snapshot.get('volatility', 0.2))
        market_cap = float(snapshot.get('market_cap', 0))

        if change > 1:
            score += 1
            signals['price_momentum'] = 'positive'
        if volume_change > 25:
            score += 1
            signals['volume_spike'] = 'confirmed'
        if snapshot.get('macd_signal') == 'bullish':
            score += 1
            signals['macd'] = 'bullish'
        if snapshot.get('moving_average_signal') == 'bullish':
            score += 1
            signals['moving_average'] = 'bullish'
        if sentiment_score > 0.25:
            score += 1
            signals['news_sentiment'] = 'positive'
        if rsi > 70:
            score -= 1
            signals['rsi'] = 'overbought'
        if market_cap >= 50_000_000_000:
            score += 0.5
            signals['large_cap_filter'] = 'passed'

        risk_score = min(100.0, max(0.0, volatility * 100 + (20 if rsi > 70 else 0)))
        confidence = min(95.0, max(35.0, 45.0 + score * 9.0 - risk_score * 0.1))

        if score >= 4:
            rec = 'BUY'
        elif score <= 1:
            rec = 'WATCH'
        else:
            rec = 'HOLD'

        horizon = 'DAILY' if volume_change > 40 else 'WEEKLY'
        explanation = (
            f'{ticker.upper()} scored {score:.1f} on the rules-v1 signal model. '
            f'The output combines momentum, volume, trend, RSI, market cap, sentiment, and volatility. '
            'This is informational only and not financial advice.'
        )

        return Recommendation(
            ticker=ticker.upper(),
            recommendation=rec,
            trade_horizon=horizon,
            confidence_score=round(confidence, 2),
            risk_score=round(risk_score, 2),
            explanation=explanation,
            supporting_signals=signals,
            timestamp=datetime.now(timezone.utc),
            model_version=self.model_version,
        )
