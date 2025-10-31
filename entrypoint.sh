#!/bin/bash

# Create tables
python -m app.init_db

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000