"""Team Task Manager REST API."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.dependencies import get_current_user, require_admin
from app.models import Task, User
from app.schemas import LoginRequest, TaskCreate, TaskPublic, TaskUpdate, TokenResponse, UserCreate, UserPublic
from app.security import create_access_token, hash_password, verify_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Team Task Manager API",
    description="A portfolio REST API demonstrating authentication, role-based authorization, SQLAlchemy persistence, and automated tests.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=email, password_hash=hash_password(payload.password), role="member")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered")
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@app.get("/users/me", response_model=UserPublic, tags=["users"])
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users", response_model=list[UserPublic], tags=["users"])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.scalars(select(User).order_by(User.id)).all()


@app.post("/tasks", response_model=TaskPublic, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(title=payload.title.strip(), description=payload.description, owner_id=current_user.id)
    if not task.title:
        raise HTTPException(status_code=422, detail="Title cannot be blank")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def task_visible_to(task: Task, user: User) -> bool:
    return user.role == "admin" or task.owner_id == user.id


@app.get("/tasks", response_model=list[TaskPublic], tags=["tasks"])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task_status: str | None = None,
):
    query = select(Task).order_by(Task.id)
    if current_user.role != "admin":
        query = query.where(Task.owner_id == current_user.id)
    if task_status is not None:
        if task_status not in {"todo", "in_progress", "done"}:
            raise HTTPException(status_code=422, detail="Invalid status filter")
        query = query.where(Task.status == task_status)
    return db.scalars(query).all()


@app.get("/tasks/{task_id}", response_model=TaskPublic, tags=["tasks"])
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if task is None or not task_visible_to(task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskPublic, tags=["tasks"])
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if task is None or not task_visible_to(task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")
    updates = payload.model_dump(exclude_unset=True)
    if "title" in updates and updates["title"] is not None:
        updates["title"] = updates["title"].strip()
        if not updates["title"]:
            raise HTTPException(status_code=422, detail="Title cannot be blank")
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if task is None or not task_visible_to(task, current_user):
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
