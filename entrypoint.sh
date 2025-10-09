#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

# Create tables
python -m app.init_db

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000