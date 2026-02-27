import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Локалӣ .env мехонад; дар Render бошад Environment Variables кор мекунанд
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError(
        "BOT_TOKEN ё CHAT_ID ёфт нашуд. "
        "Дар Render -> Service -> Environment ду variable мон: BOT_TOKEN ва CHAT_ID."
    )

app = FastAPI()

# ✅ static folder mount (фаqat агар вуҷуд дошта бошад)
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ GET / (барои Render HEAD check ҳам OK мешавад)
@app.get("/", include_in_schema=False)
def home():
    # агар index.html набошад, хатои равшан диҳем
    index_path = os.path.join("static", "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=404, detail="static/index.html not found")
    return FileResponse(index_path)

# (ихтиёрӣ, вале хуб) health endpoint
@app.get("/health", include_in_schema=False)
def health():
    return {"ok": True}

@app.post("/send_photo")
async def send_photo(photo: UploadFile = File(...)):
    """
    Frontend photo.jpg мефиристад -> Server ба Telegram мефиристад.
    """
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    content = await photo.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    files = {
        "photo": (photo.filename or "photo.jpg", content, photo.content_type or "image/jpeg")
    }
    data = {"chat_id": CHAT_ID}

    try:
        r = requests.post(tg_url, data=data, files=files, timeout=30)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Telegram request failed: {e}")

    try:
        payload = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"Telegram returned non-JSON, status={r.status_code}")

    if r.status_code != 200 or not payload.get("ok"):
        desc = payload.get("description", "Unknown telegram error")
        raise HTTPException(status_code=502, detail=desc)

    return {"ok": True}