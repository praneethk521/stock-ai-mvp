from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistItem


def list_watchlist_items(db: Session) -> list[WatchlistItem]:
    return db.query(WatchlistItem).order_by(WatchlistItem.ticker.asc()).all()


def upsert_watchlist_item(db: Session, ticker: str, notes: str = '') -> WatchlistItem:
    item = db.query(WatchlistItem).filter_by(ticker=ticker).one_or_none()
    if item:
        item.notes = notes
    else:
        item = WatchlistItem(ticker=ticker, notes=notes)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_watchlist_item(db: Session, ticker: str) -> bool:
    item = db.query(WatchlistItem).filter_by(ticker=ticker).one_or_none()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
