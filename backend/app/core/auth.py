import re

from fastapi import Header, HTTPException

from app.core.config import get_settings


USER_ID_PATTERN = re.compile(r'^[A-Za-z0-9_.@-]{1,64}$')


def get_current_user_id(x_user_id: str | None = Header(default=None)) -> str:
    user_id = (x_user_id or get_settings().default_user_id).strip()
    if not USER_ID_PATTERN.fullmatch(user_id):
        raise HTTPException(status_code=400, detail='Invalid user id')
    return user_id
