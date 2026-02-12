#!/bin/bash

# Kill any existing processes on ports 3000, 3001, 8000
echo "Cleaning up ports..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Start Backend
echo "Starting Backend..."
cd backend
if [ -d "venv" ]; then
    echo "Activating venv..."
    source venv/bin/activate
fi
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev -- -p 3001 &
FRONTEND_PID=$!
cd ..

echo "🚀 Servers started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
