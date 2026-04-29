from fastapi import FastAPI
from api.routes.chat import router as chat_router

app = FastAPI(title="Cars24 AI Buying Concierge")

app.include_router(chat_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
