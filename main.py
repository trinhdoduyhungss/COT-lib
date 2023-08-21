import uvicorn
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from api.routes import router

middleware = [
    Middleware(CORSMiddleware,
               allow_origins=["*"],
               allow_credentials=True,
               allow_methods=["*"],
               allow_headers=["*"], )
]

app = FastAPI(middleware=middleware)

app.include_router(router, prefix="")

@app.get("/")
async def root():
    """Root page."""
    return {"text": f"Hello, This is an api for COT backend"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
