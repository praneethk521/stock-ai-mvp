from sqlalchemy.orm import Session

from app.models.recommendation import RecommendationRecord
from app.schemas.market import Recommendation


def create_recommendation_record(db: Session, recommendation: Recommendation) -> RecommendationRecord:
    record = RecommendationRecord(
        ticker=recommendation.ticker,
        recommendation=recommendation.recommendation,
        trade_horizon=recommendation.trade_horizon,
        confidence_score=recommendation.confidence_score,
        risk_score=recommendation.risk_score,
        explanation=recommendation.explanation,
        supporting_signals=recommendation.supporting_signals,
        model_version=recommendation.model_version,
        generated_at=recommendation.timestamp,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_recent_recommendations(
    db: Session,
    ticker: str | None = None,
    limit: int = 20,
) -> list[RecommendationRecord]:
    query = db.query(RecommendationRecord)
    if ticker:
        query = query.filter(RecommendationRecord.ticker == ticker.upper())
    return query.order_by(RecommendationRecord.id.desc()).limit(limit).all()


def count_recommendations(db: Session) -> int:
    return db.query(RecommendationRecord).count()
