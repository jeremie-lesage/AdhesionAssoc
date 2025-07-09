# Stage 1: Frontend Builder
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend application code
COPY frontend .

# Build the frontend application
RUN npm run build

# Use a Python base image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_NAME=foyer_rural.db

# Set working directory
WORKDIR /app

# Install Node.js and npm for frontend build
# Copy backend requirements and install them
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy the rest of the application code
COPY . .

# Copy built frontend from the builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application
# The backend (main.py) will be modified to serve the frontend static files
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
