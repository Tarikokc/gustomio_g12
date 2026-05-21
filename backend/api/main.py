from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import des routers
from backend.api.routes.voicemail import router as voicemail_router

app = FastAPI(
    title="Gustomio - Voice Order Processing",
    description="Traitement automatique des commandes vocales",
    version="0.1.0"
)

# Middleware CORS (important pour Twilio)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(voicemail_router)

@app.get("/")
async def root():
    return {
        "message": "🚀 Gustomio Voice API is running!",
        "webhook_url": "/webhook/voicemail",
        "status": "ok"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
