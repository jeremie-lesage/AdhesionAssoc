# Use a Python base image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install Node.js and npm for frontend build
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install them
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy frontend package files and install dependencies
COPY frontend/package*.json ./frontend/
RUN npm install --prefix ./frontend

# Copy the rest of the application code
COPY . .

# Build the frontend application
RUN npm run build --prefix ./frontend

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application
# The backend (main.py) will be modified to serve the frontend static files
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
