from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import os
import secrets
import string
from sqlalchemy.orm import Session
from typing import List

from schemas import (
    AdhesionSchema, AdhesionCreate, ActivitySchema, ActivityCreate,
    AdminUserCreate, AdminUserOut, AdhesionPaymentUpdate,
    ContactStatus, FamilyDetails, PublicSettings
)
from auth import (
    create_access_token, get_current_admin, get_password_hash,
    verify_password
)
from rate_limiter import rate_limit
from database import create_tables, get_db
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

import crud
from config import settings

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup_event():
    create_tables()
    # Check if there is at least one admin user
    db = next(get_db())  # Get a session for startup event
    if not crud.get_admins(db):
        # If not, create a default admin user
        username = "admin"
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(12))
        hashed_password = get_password_hash(password)
        crud.create_admin(db, AdminUserCreate(username=username, password=hashed_password))
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"Default admin user created. Username: {username}, Password: {password}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    db.close()


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


@app.get("/api/config", response_model=PublicSettings)
def get_config():
    return PublicSettings(
        iban=settings.IBAN,
        bic=settings.BIC,
        bank=settings.BANK,
        postal_code_prefix=settings.POSTAL_CODE_PREFIX,
    )


# Admin login endpoint
@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = crud.get_admin_by_username(db, form_data.username)
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}


# AdhesionSchema Endpoints
@app.get("/api/adhesions", response_model=list[AdhesionSchema], dependencies=[Depends(get_current_admin)])
def list_adhesions(db: Session = Depends(get_db)):
    return crud.get_adhesions(db)


@app.post("/api/adhesions", response_model=AdhesionSchema, dependencies=[Depends(rate_limit)])
def create_adhesion(adhesion: AdhesionCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_adhesion(db, adhesion)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/adhesions/{code}", response_model=AdhesionSchema, dependencies=[Depends(rate_limit)])
def read_adhesion(code: str, db: Session = Depends(get_db)):
    adhesion = crud.get_adhesion_by_code(db, code)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="AdhesionSchema not found")
    return adhesion


@app.put("/api/adhesions/{code}/validate", response_model=AdhesionSchema, dependencies=[Depends(get_current_admin)])
async def validate_adhesion(code: str, db: Session = Depends(get_db)):
    adhesion = await crud.validate_adhesion(db, code)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="AdhesionSchema not found or already validated")
    return adhesion


@app.put("/api/adhesions/{code}/pay", response_model=AdhesionSchema, dependencies=[Depends(get_current_admin)])
def pay_adhesion(code: str, payment_update: AdhesionPaymentUpdate, db: Session = Depends(get_db)):
    adhesion = crud.update_adhesion_payment(db, code, payment_update.payment_method)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="AdhesionSchema not found")
    return adhesion


@app.put("/api/adhesions/{code}", response_model=AdhesionSchema, dependencies=[Depends(rate_limit)])
def update_adhesion(code: str, adhesion: AdhesionCreate, db: Session = Depends(get_db)):
    try:
        updated_adhesion = crud.update_adhesion(db, code, adhesion)
        if updated_adhesion is None:
            raise HTTPException(status_code=404, detail="AdhesionSchema not found")
        return updated_adhesion
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/api/adhesions/{code}/receipt", response_class=HTMLResponse)
def get_adhesion_receipt(code: str, db: Session = Depends(get_db)):
    adhesion = crud.get_adhesion_by_code(db, code)
    if adhesion is None or adhesion.status != 'paid':
        raise HTTPException(status_code=404, detail="Paid adhesion not found")

    total_cost = adhesion.adhesion_amount or 0
    activities_details = []
    for activity in adhesion.activities:
        is_resident = adhesion.ville.lower() == 'fauverney'
        price = activity.resident_price if is_resident else activity.external_price
        total_cost += price or 0
        activities_details.append({"name": activity.name, "price": price})

    context = {
        "request": {},
        "code": adhesion.code,
        "payment_date": datetime.now().strftime("%d/%m/%Y"),
        "prenom": adhesion.prenom,
        "nom": adhesion.nom,
        "email": adhesion.email,
        "payment_method": adhesion.payment_method,
        "adhesion_amount": adhesion.adhesion_amount,
        "activities": activities_details,
        "total_cost": total_cost,
    }
    return templates.TemplateResponse("receipt.html", context)


@app.delete("/api/adhesions/{code}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_adhesion(code: str, db: Session = Depends(get_db)):
    if not crud.delete_adhesion(db, code):
        raise HTTPException(status_code=404, detail="Adhesion not found")


@app.get("/api/activities/{activity_id}/adherents", response_model=list[AdhesionSchema],
         dependencies=[Depends(get_current_admin)])
def get_adherents_by_activity(activity_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_adherents_by_activity(db, activity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ActivitySchema Endpoints
@app.put("/api/activities/{activity_id}", response_model=ActivitySchema, dependencies=[Depends(get_current_admin)])
def update_activity(activity_id: int, activity: ActivityCreate, db: Session = Depends(get_db)):
    updated_activity = crud.update_activity(db, activity_id, activity)
    if updated_activity is None:
        raise HTTPException(status_code=404, detail="ActivitySchema not found")
    return updated_activity


@app.get("/api/activities", response_model=list[ActivitySchema])
def list_activities(db: Session = Depends(get_db)):
    return crud.get_activities(db)


@app.post("/api/activities", response_model=ActivitySchema, status_code=201, dependencies=[Depends(get_current_admin)])
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_activity(db, activity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/activities/{activity_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    if not crud.delete_activity(db, activity_id):
        raise HTTPException(status_code=404, detail="ActivitySchema not found")


# Admin Endpoints
@app.get("/api/admins", response_model=list[AdminUserOut], dependencies=[Depends(get_current_admin)])
def list_admins(db: Session = Depends(get_db)):
    return crud.get_admins(db)


@app.post("/api/admins", response_model=AdminUserOut, dependencies=[Depends(get_current_admin)])
def create_admin(admin: AdminUserCreate, db: Session = Depends(get_db)):
    db_admin = crud.get_admin_by_username(db, admin.username)
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(admin.password)
    admin.password = hashed_password  # Update password to hashed version before passing to crud
    return crud.create_admin(db, admin)


@app.put("/api/admins/{admin_id}", response_model=AdminUserOut, dependencies=[Depends(get_current_admin)])
def update_admin(admin_id: int, admin: AdminUserCreate, db: Session = Depends(get_db)):
    db_admin = crud.get_admin(db, admin_id)
    if not db_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    hashed_password = get_password_hash(admin.password)
    admin.password = hashed_password  # Update password to hashed version before passing to crud
    return crud.update_admin(db, admin_id, admin)


@app.delete("/api/admins/{admin_id}", status_code=204, dependencies=[Depends(get_current_admin)])
def delete_admin(admin_id: int, db: Session = Depends(get_db)):
    if not crud.delete_admin(db, admin_id):
        raise HTTPException(status_code=404, detail="Admin not found")


@app.get("/api/admin/contacts", response_model=List[ContactStatus], dependencies=[Depends(get_current_admin)])
def get_contacts(db: Session = Depends(get_db)):
    return crud.get_contacts_with_status(db)


@app.get("/api/admin/contacts/{email}", response_model=FamilyDetails, dependencies=[Depends(get_current_admin)])
def get_family_details(email: str, db: Session = Depends(get_db)):
    details = crud.get_family_details_by_email(db, email)
    if not details:
        raise HTTPException(status_code=404, detail="No adhesions found for this email")
    return details
