FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ ./backend/

# Copy dashboard files
COPY dashboard/ ./dashboard/

# Copy frontend files
COPY frontend/ ./frontend/

# Copy .env file
COPY .env .

# Expose port
EXPOSE 8000

# Run the application from backend directory
CMD ["python", "backend/server.py"]