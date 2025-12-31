import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_FILE = "matchmaking.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_number TEXT NOT NULL,
            gender TEXT NOT NULL,
            interested_in TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            looking_for TEXT NOT NULL,
            about_me TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "processed": False})

@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap(request: Request):
    return templates.TemplateResponse("roadmap.html", {"request": request})

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    student_number: str = Form(...),
    gender: str = Form(...),
    interested_in: str = Form(...),
    whatsapp: str = Form(...),
    looking_for: str = Form(...),
    about_me: str = Form(...)
):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, student_number, gender, interested_in, whatsapp, looking_for, about_me)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, student_number, gender, interested_in, whatsapp, looking_for, about_me))
    conn.commit()
    conn.close()
    
    return templates.TemplateResponse("index.html", {"request": request, "processed": True})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
