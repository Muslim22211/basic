import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN ё CHAT_ID дар .env нест")

app = FastAPI()

# static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/send_photo")
async def send_photo(photo: UploadFile = File(...)):
    """
    Frontend photo.jpg мефиристад -> Server ба Telegram мефиристад.
    """
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    # UploadFile-ро мехонем
    content = await photo.read()

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