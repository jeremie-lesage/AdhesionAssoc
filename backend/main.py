from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

from models import AdminLogin, Adhesion, AdhesionCreate, Activity, ActivityCreate
from auth import verify_admin_token, ADMIN_PASSWORD, ADMIN_TOKEN
from rate_limiter import rate_limit
from database import create_tables
import crud

app = FastAPI()

# Print admin password and token on startup
print(f"\nADMIN PASSWORD (for /api/admin/login): {ADMIN_PASSWORD}\n")

# CORS Middleware
origins = [
    "http://localhost:5173", # Frontend development server
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
@app.post("/api/admin/login", dependencies=[Depends(rate_limit)])
async def admin_login(admin_user: AdminLogin):
    if admin_user.username == "admin" and admin_user.password == ADMIN_PASSWORD:
        return {"access_token": ADMIN_TOKEN, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Adhesion Endpoints
@app.get("/api/adhesions", response_model=list[Adhesion], dependencies=[Depends(verify_admin_token)])
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


@app.put("/api/adhesions/{code}/validate", response_model=Adhesion, dependencies=[Depends(verify_admin_token)])
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
         dependencies=[Depends(verify_admin_token)])
def get_adherents_by_activity(activity_id: int):
    try:
        return crud.get_adherents_by_activity(activity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Activity Endpoints
@app.put("/api/activities/{activity_id}", response_model=Activity, dependencies=[Depends(verify_admin_token)])
def update_activity(activity_id: int, activity: ActivityCreate):
    updated_activity = crud.update_activity(activity_id, activity)
    if updated_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return updated_activity


@app.get("/api/activities", response_model=list[Activity])
def list_activities():
    return crud.get_activities()


@app.post("/api/activities", response_model=Activity, status_code=201, dependencies=[Depends(verify_admin_token)])
def create_activity(activity: ActivityCreate):
    try:
        return crud.create_activity(activity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/activities/{activity_id}", status_code=204, dependencies=[Depends(verify_admin_token)])
def delete_activity(activity_id: int):
    if not crud.delete_activity(activity_id):
        raise HTTPException(status_code=404, detail="Activity not found")


# # Mount static files for the frontend
# app.mount("/", StaticFiles(directory="./frontend/dist", html=True), name="static")


# @app.get("/")
# def serve_frontend(request: Request):
#     with open(os.path.join("./frontend/dist", "index.html"), "r") as f:
#         html_content = f.read()

#     backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
#     html_content = html_content.replace("<!-- BACKEND_URL_PLACEHOLDER -->",
#                                         f"<script>window.BACKEND_URL = '{backend_url}';</script>")

#     return HTMLResponse(content=html_content, status_code=200)


# Initialize database tables
create_tables()