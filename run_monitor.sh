#!/bin/bash

# Start the backend
cd backend
uv pip install -r requirements.txt
uvicorn app.main:app --host localhost --port 8000 --reload &

# Start the frontend
cd ../frontend
npm install
npm start

# Wait for both processes
wait 