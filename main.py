import os
import time
from typing import List, Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pymongo import MongoClient
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import uvicorn
import uuid 

# 1. SETUP ENV & GROQ
load_dotenv()
api_key = os.getenv("API_KEY") 


if not api_key:
    print("WARNING: API Key not found. Chat will fail.")

client = Groq(api_key=api_key)

# 2. SETUP APP
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- DEBUGGER: PRINTS ERROR DETAILS TO TERMINAL ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("\n--- ⚠️ VALIDATION ERROR ⚠️ ---")
    print(f"Error Details: {exc.errors()}")
    # print(f"Raw Data Received: {await request.body()}") 
    print("--------------------------------\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# 3. MONGODB CONNECTION
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["fitness_db"]
users_collection = db["users"]
history_collection = db["chat_history"] 

# 4. DATA MODELS
class ChatRequest(BaseModel):
    message: str
    username: str
    session_id: str 

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# --- API ENDPOINTS (The Logic) ---

# 1. GET USER HISTORY
@app.post("/api/get_history")
async def get_history(request: Request):
    data = await request.json()
    username = data.get("username")
    
    cursor = history_collection.find({"username": username}).sort("timestamp", -1)
    
    history_list = []
    for doc in cursor:
        history_list.append({
            "session_id": doc["session_id"],
            "title": doc.get("title", "New Chat")
        })
    
    return JSONResponse(content={"history": history_list})

# 2. LOAD SPECIFIC CHAT (RESTORED FUNCTION)
@app.post("/api/load_chat")
async def load_chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    
    chat_doc = history_collection.find_one({"session_id": session_id})
    if chat_doc:
        return JSONResponse(content={"messages": chat_doc.get("messages", [])})
    return JSONResponse(content={"messages": []})

# 3. SEND MESSAGE
@app.post("/api/chat")
async def chat_endpoint(chat_data: ChatRequest):  # <--- RENAMED 'request' to 'chat_data'
    # Use 'chat_data' to access the fields
    user_msg = chat_data.message
    username = chat_data.username
    session_id = chat_data.session_id

    # -- 1. CHECK FOR EXISTING SESSION --
    chat_doc = history_collection.find_one({"session_id": session_id})
    
    if not chat_doc:
        title = user_msg[:30] + "..." 
        chat_doc = {
            "session_id": session_id,
            "username": username,
            "title": title,
            "messages": [],
            "timestamp": time.time()
        }
        history_collection.insert_one(chat_doc)

    # -- 2. CALL GROQ API --
    try:
        system_prompt = "You are MALAYSIAN GymBro, a friendly Malaysian personal trainer. Keep answers short, punchy, motivating, Professional, Easy to understand. Use English, Malay, or Manglish. Only talk about gym, fitness, diet, and healthy lifestyle. Reject anything outside those topics."
        
        existing_msgs = chat_doc.get("messages", [])[-5:] 
        
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in existing_msgs:
            role = "user" if m.get('sender') == 'user' else "assistant"
            api_messages.append({"role": role, "content": m['text']})
        
        api_messages.append({"role": "user", "content": user_msg})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=api_messages,
            temperature=0.8
        )
        
        bot_reply = completion.choices[0].message.content

        # -- 3. SAVE TO DB --
        new_messages = [
            {"sender": "user", "text": user_msg},
            {"sender": "bot", "text": bot_reply}
        ]
        
        history_collection.update_one(
            {"session_id": session_id},
            {"$push": {"messages": {"$each": new_messages}}}
        )

        return JSONResponse(content={"reply": bot_reply})

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"reply": f"Alamak bro, server crash! {str(e)}"})


# --- LOGIN / SIGNUP LOGIC ---

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match!"})
    if users_collection.find_one({"username": username}):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username taken!"})
    
    users_collection.insert_one({"username": username, "email": email, "password": password})
    return RedirectResponse(url="/login", status_code=303)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username})
    if not user or user["password"] != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    return RedirectResponse(url="/chat", status_code=303)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)