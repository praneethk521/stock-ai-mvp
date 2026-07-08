from datetime import datetime, timezone
from typing import Any

from app.schemas.market import ExplanationResponse, Recommendation


class ExplanationService:
    model_version = 'explanation-fallback-v1'

    def generate(
        self,
        ticker: str,
        recommendation: Recommendation,
        snapshot: dict[str, Any],
        sentiment_score: float,
    ) -> ExplanationResponse:
        signal_summary = self._signal_summary(recommendation.supporting_signals)
        risk_notes = self._risk_notes(recommendation.risk_score, snapshot)
        narrative = (
            f'{ticker.upper()} is rated {recommendation.recommendation} for a {recommendation.trade_horizon.lower()} horizon. '
            f'The fallback explanation weighs price action, trend, volatility, market cap, and news sentiment. '
            f'Current sentiment score is {sentiment_score:.2f}, with confidence at {recommendation.confidence_score:.1f}% '
            f'and risk at {recommendation.risk_score:.1f}%.'
        )
        return ExplanationResponse(
            ticker=ticker.upper(),
            recommendation=recommendation.recommendation,
            narrative=narrative,
            signal_summary=signal_summary,
            risk_notes=risk_notes,
            generated_at=datetime.now(timezone.utc),
            model_version=self.model_version,
            provider='rules-fallback',
        )

    def _signal_summary(self, signals: dict[str, Any]) -> list[str]:
        if not signals:
            return ['No strong positive or negative signals were detected by the rules engine.']
        return [f'{key.replace("_", " ")}: {value}' for key, value in signals.items()]

    def _risk_notes(self, risk_score: float, snapshot: dict[str, Any]) -> list[str]:
        notes: list[str] = []
        if risk_score >= 70:
            notes.append('Risk is elevated; position sizing and time horizon matter.')
        elif risk_score >= 40:
            notes.append('Risk is moderate; watch volatility and confirmation signals.')
        else:
            notes.append('Risk is comparatively contained under the current rules model.')
        if float(snapshot.get('rsi', 50)) > 70:
            notes.append('RSI is overbought, which can increase pullback risk.')
        if float(snapshot.get('volatility', 0.25)) > 0.4:
            notes.append('Volatility is above the default watch threshold.')
        return notes
