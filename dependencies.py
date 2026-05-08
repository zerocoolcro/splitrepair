from fastapi import WebSocket, status
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM
from database import SessionLocal
from models import User

async def get_current_user_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user
    finally:
        db.close()
