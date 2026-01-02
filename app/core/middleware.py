"""
Middleware module
"""

from typing import Optional

from fastapi import Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware


# Define your user model
class User(BaseModel):
    """
    Place holder model django old code base
    """

    id: int
    username: str
    email: Optional[str] = None
    roles: list[str] = []


class UserInjectionMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Default: unauthenticated
        request.scope["user"] = User(id=1, username="system")
        request.scope["auth"] = None

        # auth = request.headers.get("authorization")

        response = await call_next(request)
        return response

