from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import os
import secrets
import string

from models import (
    Adhesion, AdhesionCreate, Activity, ActivityCreate,
    AdminUser, AdminUserCreate
)
from auth import (
    create_access_token, get_current_admin, get_password_hash,
    verify_password
)
from rate_limiter import rate_limit
from database import create_tables
import crud

app = FastAPI()


@app.on_event("startup")
def startup_event():
    create_tables()
    # Check if there is at least one admin user
    if not crud.get_admins():
        # If not, create a default admin user
        username = "admin"
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(12))
        hashed_password = get_password_hash(password)
        crud.create_admin({"username": username, "hashed_password": hashed_password})
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"Default admin user created. Username: {username}, Password: {password}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


# CORS Middleware
origins = [
    "http://localhost:5173",  # Frontend development server
    os.environ.get("BACKEND_URL", "http://localhost:8000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)


# Admin login endpoint
@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = crud.get_admin_by_username(form_data.username)
    if not admin or not verify_password(form_data.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": admin["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


# Adhesion Endpoints
@app.get("/api/adhesions", response_model=list[Adhesion], dependencies=[Depends(get_current_admin)])
def list_adhesions():
    return crud.get_adhesions()


@app.post("/api/adhesions", response_model=Adhesion, dependencies=[Depends(rate_limit)])
def create_adhesion(adhesion: AdhesionCreate):
    try:
        return crud.create_adhesion(adhesion)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/adhesions/{code}", response_model=Adhesion, dependencies=[Depends(rate_limit)])
def read_adhesion(code: str):
    adhesion = crud.get_adhesion_by_code(code)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="Adhesion not found")
    return adhesion


@app.put("/api/adhesions/{code}/validate", response_model=Adhesion, dependencies=[Depends(get_current_admin)])
def validate_adhesion(code: str):
    adhesion = crud.validate_adhesion(code)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="Adhesion not found or already validated")
    return adhesion


@app.put("/api/adhesions/{code}", response_model=Adhesion, dependencies=[Depends(rate_limit)])
def update_adhesion(code: str, adhesion: AdhesionCreate):
    try:
        updated_adhesion = crud.update_adhesion(code, adhesion)
        if updated_adhesion is None:
            raise HTTPException(status_code=404, detail="Adhesion not found")
        return updated_adhesion
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/api/activities/{activity_id}/adherents", response_model=list[Adhesion],
         dependencies=[Depends(get_current_admin)])
def get_adherents_by_activity(activity_id: int):
    try:
        return crud.get_adherents_by_activity(activity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Activity Endpoints
@app.put("/api/activities/{activity_id}", response_model=Activity, dependencies=[Depends(get_current_admin)])
def update_activity(activity_id: int, activity: ActivityCreate):
    updated_activity = crud.update_activity(activity_id, activity)
    if updated_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return updated_activity


@app.get("/api/activities", response_model=list[Activity])
def list_activities():
    return crud.get_activities()


@app.post("/api/activities", response_model=Activity, status_code=201, dependencies=[Depends(get_current_admin)])
def create_activity(activity: ActivityCreate):
    try:
        return crud.create_activity(activity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/activities/{activity_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_activity(activity_id: int):
    if not crud.delete_activity(activity_id):
        raise HTTPException(status_code=404, detail="Activity not found")


# Admin Endpoints
@app.get("/api/admins", response_model=list[AdminUser], dependencies=[Depends(get_current_admin)])
def list_admins():
    return crud.get_admins()


@app.post("/api/admins", response_model=AdminUser, dependencies=[Depends(get_current_admin)])
def create_admin(admin: AdminUserCreate):
    db_admin = crud.get_admin_by_username(admin.username)
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(admin.password)
    return crud.create_admin({"username": admin.username, "hashed_password": hashed_password})


@app.put("/api/admins/{admin_id}", response_model=AdminUser, dependencies=[Depends(get_current_admin)])
def update_admin(admin_id: int, admin: AdminUserCreate):
    db_admin = crud.get_admin(admin_id)
    if not db_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    hashed_password = get_password_hash(admin.password)
    return crud.update_admin(admin_id, {"username": admin.username, "hashed_password": hashed_password})


@app.delete("/api/admins/{admin_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_admin(admin_id: int):
    if not crud.delete_admin(admin_id):
        raise HTTPException(status_code=404, detail="Admin not found")
