# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os, shutil, sqlite3, datetime, hashlib

APP_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATABASE = os.path.join(APP_DIR, "repair_map.db")
ADMIN_TOKEN = "change_this_to_secure_token"  # promijeni prije produkcije

app = FastAPI(title="Split Repair Map - API (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # proizvodno ograniči na front-end domenu
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB helper ---
def get_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS issues (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      category TEXT,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      address TEXT,
      photo_path TEXT,
      status TEXT NOT NULL DEFAULT 'zaprimljeno',
      votes INTEGER NOT NULL DEFAULT 0,
      reporter_name TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS comments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      issue_id INTEGER,
      author TEXT,
      message TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS admins (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE,
      password_hash TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

# --- Pydantic schemas ---
class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None
    reporter_name: Optional[str] = None

class IssueOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    latitude: float
    longitude: float
    address: Optional[str]
    photo_url: Optional[str]
    status: str
    votes: int
    reporter_name: Optional[str]
    created_at: str
    updated_at: str

# --- Helpers ---
def save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1]
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    fname = f"{stamp}{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    with open(fpath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return fpath

def row_to_issue(row):
    if not row:
        return None
    photo_path = row["photo_path"]
    photo_url = None
    if photo_path:
        photo_url = f"/photo/{os.path.basename(photo_path)}"
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "address": row["address"],
        "photo_url": photo_url,
        "status": row["status"],
        "votes": row["votes"],
        "reporter_name": row["reporter_name"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

# --- Endpoints ---
@app.post("/issues", response_model=IssueOut)
async def create_issue(
    title: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    reporter_name: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    photo_path = None
    if photo:
        photo_path = save_upload(photo)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO issues (title, description, category, latitude, longitude, address, photo_path, reporter_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, category, latitude, longitude, address, photo_path, reporter_name)
    )
    conn.commit()
    iid = cur.lastrowid
    row = cur.execute("SELECT * FROM issues WHERE id = ?", (iid,)).fetchone()
    conn.close()
    return row_to_issue(row)

@app.get("/issues", response_model=List[IssueOut])
def list_issues(skip: int = 0, limit: int = 100, status: Optional[str] = None):
    conn = get_db()
    cur = conn.cursor()
    if status:
        rows = cur.execute("SELECT * FROM issues WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?", (status, limit, skip)).fetchall()
    else:
        rows = cur.execute("SELECT * FROM issues ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, skip)).fetchall()
    conn.close()
    return [row_to_issue(r) for r in rows]

@app.get("/issues/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    return row_to_issue(row)

@app.post("/issues/{issue_id}/vote")
def vote_issue(issue_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE issues SET votes = votes + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (issue_id,))
    conn.commit()
    row = cur.execute("SELECT votes FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"issue_id": issue_id, "votes": row["votes"]}

@app.put("/issues/{issue_id}/status")
def update_status(issue_id: int, status: str = Form(...), token: str = Form(...)):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE issues SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, issue_id))
    conn.commit()
    row = cur.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    return row_to_issue(row)

@app.get("/photo/{fname}")
def get_photo(fname: str):
    fpath = os.path.join(UPLOAD_DIR, fname)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404)
    return FileResponse(fpath)
