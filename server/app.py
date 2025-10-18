from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WSD Backend (Scaffold)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend scaffold running"}

@app.post("/api/lesk/wordnet")
async def lesk_wordnet():
    return {"todo": "implement WordNet Lesk"}

@app.post("/api/lesk/wiki")
async def lesk_wiki():
    return {"todo": "implement Wikipedia-based Lesk"}
