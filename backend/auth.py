from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import uuid

ADMIN_PASSWORD = secrets.token_urlsafe(16)
ADMIN_TOKEN = str(uuid.uuid4())

print(f"\nADMIN PASSWORD (for /api/admin/login): {ADMIN_PASSWORD}\n")

security = HTTPBearer()

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

