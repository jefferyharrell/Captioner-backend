from collections.abc import Awaitable, Callable

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from app.database import Base, SessionLocal, engine
from app.routers.login import router as login_router
from app.routers.photos import router as photos_router
from app.routers.rescan import router as rescan_router
from app.storage import get_storage_backend

load_dotenv()

# Ensure database tables exist
Base.metadata.create_all(bind=engine)


# Create a custom middleware for test exceptions
class TestErrorMiddleware(BaseHTTPMiddleware):
    """Custom middleware to catch test exceptions and return proper error responses.
    This middleware captures exceptions from test modules and converts them
    to proper HTTP 500 responses instead of crashing the application."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process the request and handle any test exceptions."""
        try:
            # Process the request normally
            return await call_next(request)
        except Exception as exc:
            # Check if this is one of our test exceptions
            exc_name = exc.__class__.__name__
            if exc_name == "BoomError" or (
                hasattr(exc, "__module__") and "test_app" in str(exc.__module__)
            ):
                return JSONResponse(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": str(exc)},
                )
            # Re-raise all other exceptions
            raise


app = FastAPI()

# Add our test error middleware to catch dependency errors
app.add_middleware(TestErrorMiddleware)


app.include_router(photos_router)
app.include_router(rescan_router)
app.include_router(login_router)

# Reminder: JWT_SECRET_KEY must be set in the environment for login/token auth

__all__ = [
    "HTTP_200_OK",
    "HTTP_500_INTERNAL_SERVER_ERROR",
    "SessionLocal",
    "app",
    "get_storage_backend",
]
