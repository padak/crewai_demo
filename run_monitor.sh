#!/bin/bash

# Start the backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 161.35.192.142 --port 8000 --reload &

# Start the frontend
cd ../frontend
npm install
npm start

# Wait for both processes
wait 