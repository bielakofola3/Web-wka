from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from .models import get_db, User, Post, Comment
from .auth import (
    hash_password, verify_password, get_user_by_username, get_user_by_email,
    create_user, is_common_password
)
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("mycoforum.security")
logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(20).all()
    user = get_current_user(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts, "user": user})

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if is_common_password(password):
        return templates.TemplateResponse("register.html", {
            "request": request, "error": "Hasło zbyt słabe lub popularne (min. 8 znaków)"
        })
    if get_user_by_username(db, username) or get_user_by_email(db, email):
        return templates.TemplateResponse("register.html", {
            "request": request, "error": "Użytkownik lub email już istnieje"
        })
    user = create_user(db, username, email, password)
    logger.info(f"Nowa rejestracja: {username} z IP {request.client.host}")
    return RedirectResponse("/login", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        logger.warning(f"Nieudane logowanie: {username} z IP {request.client.host}")
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Nieprawidłowy login lub hasło"
        })
    # Nowa sesja
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    logger.info(f"Logowanie: {username} z IP {request.client.host}")
    return RedirectResponse("/", status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@router.get("/post/new", response_class=HTMLResponse)
def new_post_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("new_post.html", {"request": request, "user": user})

@router.post("/post/new")
def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    # Walidacja
    if len(title) < 3 or len(title) > 200 or len(content) < 10:
        raise HTTPException(status_code=400, detail="Nieprawidłowe dane")
    post = Post(title=title.strip(), content=content.strip(), author_id=user.id)
    db.add(post)
    db.commit()
    return RedirectResponse(f"/post/{post.id}", status_code=303)

@router.get("/post/{post_id}", response_class=HTMLResponse)
def view_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    user = get_current_user(request, db)
    return templates.TemplateResponse("post.html", {
        "request": request, "post": post, "user": user, "comments": post.comments
    })

@router.post("/post/{post_id}/comment")
def add_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    if len(content) < 2:
        raise HTTPException(status_code=400)
    comment = Comment(content=content.strip(), author_id=user.id, post_id=post_id)
    db.add(comment)
    db.commit()
    return RedirectResponse(f"/post/{post_id}", status_code=303)

@router.post("/post/{post_id}/delete")
def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or not user or post.author_id != user.id:
        raise HTTPException(status_code=403)
    db.delete(post)
    db.commit()
    return RedirectResponse("/", status_code=303)

# Podobnie edycja – do dodania
