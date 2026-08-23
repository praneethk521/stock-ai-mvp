from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.price_alert import PriceAlert


def list_price_alerts(
    db: Session,
    *,
    user_id: str,
    active_only: bool = False,
) -> list[PriceAlert]:
    query = db.query(PriceAlert).filter_by(user_id=user_id)
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(PriceAlert.is_active.desc(), PriceAlert.created_at.desc()).all()


def count_price_alerts(db: Session, *, user_id: str | None = None) -> int:
    query = db.query(PriceAlert)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.count()


def create_price_alert(
    db: Session,
    *,
    user_id: str,
    ticker: str,
    condition: str,
    target_price: float,
) -> PriceAlert:
    alert = PriceAlert(
        user_id=user_id,
        ticker=ticker,
        condition=condition,
        target_price=target_price,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def update_price_alert(
    db: Session,
    *,
    alert_id: int,
    user_id: str,
    condition: str | None = None,
    target_price: float | None = None,
    is_active: bool | None = None,
) -> PriceAlert | None:
    alert = db.query(PriceAlert).filter_by(id=alert_id, user_id=user_id).one_or_none()
    if alert is None:
        return None
    if condition is not None:
        alert.condition = condition
    if target_price is not None:
        alert.target_price = target_price
    if is_active is not None:
        alert.is_active = is_active
        if is_active:
            alert.triggered_at = None
    db.commit()
    db.refresh(alert)
    return alert


def delete_price_alert(db: Session, *, alert_id: int, user_id: str) -> bool:
    alert = db.query(PriceAlert).filter_by(id=alert_id, user_id=user_id).one_or_none()
    if alert is None:
        return False
    db.delete(alert)
    db.commit()
    return True


def evaluate_price_alerts(
    db: Session,
    *,
    alerts: list[PriceAlert],
    prices: dict[str, float],
) -> list[PriceAlert]:
    now = datetime.now(timezone.utc)
    for alert in alerts:
        current_price = prices[alert.ticker]
        alert.last_price = current_price
        triggered = (alert.condition == 'above' and current_price >= alert.target_price) or (
            alert.condition == 'below' and current_price <= alert.target_price
        )
        if triggered:
            alert.is_active = False
            alert.triggered_at = now
    db.commit()
    for alert in alerts:
        db.refresh(alert)
    return alerts
