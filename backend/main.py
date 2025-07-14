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
    """
    Handles the login functionality for admin users by verifying the provided
    credentials. If the login details are correct, it returns a JSON response
    containing an access token and its type. If authentication fails, an
    HTTPException with status code 401 is raised.

    :param admin_user: An instance of AdminLogin containing the username and
        password for authentication.
    :returns: A dictionary with the access token and its type if the provided
        credentials are valid.
    :raises HTTPException: If the authentication fails due to incorrect
        username or password.
    """
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
    """
    Retrieves a list of adhesions.

    This function handles the GET request to fetch a list of all adhesions
    in the system. It uses dependency injection to ensure that the user
    has administrative privileges via token verification before granting access.

    :dependencies:
        * verify_admin_token: Middleware that verifies if a valid admin token
          is provided.

    :return: List of all adhesions retrieved from the system.
    :rtype: list[Adhesion]
    """
    return crud.get_adhesions()


@app.post("/api/adhesions", response_model=Adhesion, dependencies=[Depends(rate_limit)])
def create_adhesion(adhesion: AdhesionCreate):
    """
    Creates a new adhesion record in the system. The function is responsible
    for handling the creation process of an adhesion instance and ensures
    appropriate rate-limiting measures are applied. If any validation
    or business logic error occurs during the creation process, an HTTP
    exception with a 400 status code is raised.

    :param adhesion: The adhesion data provided by the user to create a new adhesion entry.
    :type adhesion: AdhesionCreate
    :return: The newly created adhesion instance.
    :rtype: Adhesion
    :raises HTTPException: If a ValueError occurs during adhesion creation.
    """
    try:
        return crud.create_adhesion(adhesion)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/adhesions/{code}", response_model=Adhesion, dependencies=[Depends(rate_limit)])
def read_adhesion(code: str):
    """
    Fetch an adhesion resource by its unique identifier.

    This function retrieves an adhesion object from the database using
    its unique code. The retrieved adhesion data is returned in
    the form of the specified response model. If the adhesion is
    not found, an HTTP 404 error is raised with a descriptive detail.

    :param code: The unique identifier of the adhesion to be fetched.
    :type code: str
    :return: The adhesion associated with the provided code.
    :rtype: Adhesion
    :raises HTTPException: If the adhesion is not found.
    """
    adhesion = crud.get_adhesion_by_code(code)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="Adhesion not found")
    return adhesion


@app.put("/api/adhesions/{code}/validate", response_model=Adhesion, dependencies=[Depends(verify_admin_token)])
def validate_adhesion(code: str):
    """
    Validates an adhesion identified by the given code and marks it as validated.

    This endpoint allows for an adhesion to be validated if it has not been
    validated already. Only an administrator with a verified token can
    invoke this operation. If the adhesion does not exist or has already
    been validated, an HTTP 404 error is raised.

    :param code: A unique string representing the code of the adhesion
                 to be validated.
    :type code: str

    :return: The validated Adhesion object.
    :rtype: Adhesion
    """
    adhesion = crud.validate_adhesion(code)
    if adhesion is None:
        raise HTTPException(status_code=404, detail="Adhesion not found or already validated")
    return adhesion


@app.put("/api/adhesions/{code}", response_model=Adhesion, dependencies=[Depends(rate_limit)])
def update_adhesion(code: str, adhesion: AdhesionCreate):
    """
    Updates an existing adhesion by its unique code. This endpoint allows for
    modifying the properties of an adhesion using the provided data. If the adhesion
    with the given code does not exist, a 404 error is raised. In case of validation
    errors or other issues, appropriate HTTP exceptions are returned.

    :param code:
        The unique identifier of the adhesion to update.
    :type code: str
    :param adhesion:
        The updated data for the adhesion.
    :type adhesion: AdhesionCreate
    :return:
        The updated adhesion object if the operation is successful.
    :rtype: Adhesion
    """
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
    """
    Fetch adherents related to a specific activity.

    This function handles a GET request to retrieve a list of adherents associated
    with the specified activity ID. It enforces admin-level access through token
    verification. If the specified activity ID cannot be found, it raises an HTTP
    404 error.

    :param activity_id: The ID of the activity for which adherents need to
        be retrieved.
    :type activity_id: int
    :return: A list of adherents associated with the given activity ID.
    :rtype: list[Adhesion]
    :raises HTTPException: If the activity ID is invalid or does not exist
        (status code 404).
    """
    try:
        return crud.get_adherents_by_activity(activity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Activity Endpoints
@app.put("/api/activities/{activity_id}", response_model=Activity, dependencies=[Depends(verify_admin_token)])
def update_activity(activity_id: int, activity: ActivityCreate):
    """
    Updates an existing activity in the system. This operation allows administrators to
    modify details of an activity based on the input provided. The endpoint uses
    dependency injection to ensure only authenticated administrators can perform this action.
    If the activity with the specified ID does not exist, a 404 error is raised.

    :param activity_id: The unique identifier of the activity to be updated.
    :type activity_id: int
    :param activity: The new data for updating the activity.
    :type activity: ActivityCreate
    :return: The updated activity object as per the response model.
    :rtype: Activity
    :raises HTTPException: If the activity with the specified ID is not found.
    """
    updated_activity = crud.update_activity(activity_id, activity)
    if updated_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return updated_activity


@app.get("/api/activities", response_model=list[Activity])
def list_activities():
    """
    Fetches a list of activities.

    This function interacts with the CRUD layer to retrieve a list of
    activities. The data is returned in a format suitable for the specified
    `response_model`. Typically used to provide a read-only API endpoint
    to clients requesting details about available activities.

    :raises HTTPException: If there is an error during the retrieval of activities.
    :rtype: list[Activity]
    :return: List of activities retrieved from the database.
    """
    return crud.get_activities()


@app.post("/api/activities", response_model=Activity, status_code=201, dependencies=[Depends(verify_admin_token)])
def create_activity(activity: ActivityCreate):
    """
    Creates a new activity using the provided activity data.

    :param activity: The new activity data to be created.
    :type activity: ActivityCreate
    :return: The newly created activity.
    :rtype: Activity
    :raises HTTPException: If the activity creation fails due to invalid input,
        an HTTP 400 exception with the error details will be raised.
    """
    try:
        return crud.create_activity(activity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/activities/{activity_id}", status_code=204, dependencies=[Depends(verify_admin_token)])
def delete_activity(activity_id: int):
    """
    Deletes an activity based on the provided activity ID. Only administrators are allowed
    to access this endpoint. If the activity with the specified ID does not exist, a 404
    error will be returned.

    :param activity_id: The unique identifier of the activity to be deleted
    :type activity_id: int
    :return: None
    """
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