from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from .api.auth import router as auth_router
from .api.videos_api import router_videos

app = FastAPI()

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(router_videos, prefix="/api/videos", tags=["videos"])


@app.get("/")
def health_check():
    return {"message": "ANB Rising Stars Showcase API"}


# Custom Exception Handler
@app.exception_handler(HTTPException)
async def custom_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content=exc.detail,
                        headers=exc.headers)
