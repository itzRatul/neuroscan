import logging
import uuid
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests

from chat_service import ChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ChatBackend")

chat_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global chat_service
    logger.info("Starting Chat Backend...")
    chat_service = ChatService()
    logger.info("Chat Backend Ready!")
    yield
    logger.info("Shutting down Chat Backend.")

app = FastAPI(title="NeuroScan AI Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "NeuroScan AI Chat Backend",
        "message": "Welcome to NeuroScan AI Chat API!"
    }

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class TestResultSync(BaseModel):
    session_id: str
    result_data: dict

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not ready")
    
    session_id = request.session_id or uuid.uuid4().hex
    try:
        response_text = chat_service.process_message(session_id, request.message)
        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/webhook/test_result")
async def sync_test_result(data: TestResultSync):
    """
    Called by the main analysis backend when a test is complete.
    """
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not ready")
    
    chat_service.update_test_result(data.session_id, data.result_data)
    return {"status": "success"}

def process_telegram_photo_task(bot_token: str, chat_id: int, session_id: str, file_id: str):
    # Send typing action
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})
    
    try:
        # Download file from Telegram
        file_info = requests.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        img_data = requests.get(file_url).content
        
        # Send to Main Backend
        main_backend_url = os.getenv("MAIN_BACKEND_URL", "http://localhost:8000").rstrip("/")
        api_key = os.getenv("NEUROSCAN_API_KEY", "")
        
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key
            
        files = {"file": ("photo.jpg", img_data, "image/jpeg")}
        data_payload = {"session_id": session_id} 
        
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
            "chat_id": chat_id,
            "text": "⏳ Processing your face scan... This takes a few seconds."
        })
        
        resp = requests.post(f"{main_backend_url}/analyze", files=files, data=data_payload, headers=headers, timeout=90)
        
        if resp.status_code == 200:
            result = resp.json()
            
            # Save test result locally to support conversational follow-up
            result_data = {
                "features": result.get("features", {}),
                "feature_flags": result.get("feature_flags", {}),
                "prediction": result.get("prediction", {})
            }
            if chat_service:
                chat_service.update_test_result(session_id, result_data)
            
            prediction = result.get("prediction", {})
            risk_level = prediction.get("risk_level", "Unknown")
            score = prediction.get("percentage", 0)
            
            caption = (
                f"🩺 *NeuroScan Analysis Complete*\n\n"
                f"*Asymmetry Score:* {score}%\n"
                f"*Risk Level:* {risk_level}\n\n"
                f"I have saved this result. You can now ask me any questions about it!"
            )
            
            # The returned URLs from main backend are relative to its host (e.g. /results/...)
            annotated_url = main_backend_url + result.get("annotated_image_url", "")
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendPhoto", json={
                "chat_id": chat_id,
                "photo": annotated_url,
                "caption": caption,
                "parse_mode": "Markdown"
            })
            
            pdf_url = main_backend_url + result.get("pdf_url", "")
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", json={
                "chat_id": chat_id,
                "document": pdf_url
            })
            
        else:
            err_msg = resp.json().get("detail", "Failed to analyze photo.")
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"❌ Error: {err_msg}"
            })
            
    except Exception as e:
        logger.exception("Error processing Telegram photo:")
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
            "chat_id": chat_id,
            "text": "❌ An error occurred while processing your photo."
        })

# --- TELEGRAM BOT WEBHOOK ---
# To use Telegram, set webhook: https://api.telegram.org/bot<TOKEN>/setWebhook?url=<YOUR_URL>/webhook/telegram
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    if not chat_service:
        return {"status": "not ready"}
        
    data = await request.json()
    if "message" not in data:
        return {"status": "ok"}
        
    message = data["message"]
    chat_id = message["chat"]["id"]
    session_id = str(chat_id)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Cannot process Telegram webhook.")
        return {"status": "error", "message": "token not set"}

    # 1. Handle Photo Uploads
    if "photo" in message:
        photo = message["photo"][-1] # Largest photo
        file_id = photo["file_id"]
        background_tasks.add_task(process_telegram_photo_task, bot_token, chat_id, session_id, file_id)
        return {"status": "ok"}
        
    # 2. Handle Text Messages
    text = message.get("text", "")
    if text:
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})
        
        if text == "/start":
            response_text = "Welcome to NeuroScan Bot! 🧠\n\nYou can send me a clear, front-facing headshot to get a stroke risk analysis, or simply chat with me about stroke symptoms and prevention."
        else:
            response_text = chat_service.process_message(session_id, text)
        
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": response_text}
        )
            
    return {"status": "ok"}

