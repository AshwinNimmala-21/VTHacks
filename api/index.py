from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import Optional

# Create FastAPI app
app = FastAPI(title="Woke AI Platform", description="Premium in-house services with AI-powered matching")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for now to avoid Supabase issues
mock_data = {
    "users": [
        {"id": "user1", "email": "test@example.com", "password": "password123", "name": "Test User"}
    ],
    "tasks": [],
    "bookings": [],
    "taskers": [
        {"id": "tasker1", "name": "John Smith", "skills": ["Cleaning"], "hourly_rate": 25, "bio": "Professional cleaner"},
        {"id": "tasker2", "name": "Sarah Johnson", "skills": ["Beauty"], "hourly_rate": 35, "bio": "Beauty expert"}
    ]
}

# Pydantic models
class CustomerRegister(BaseModel):
    name: str
    email: str
    password: str

class CustomerLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    customer_id: str
    status: Optional[str] = "open"

class BookingCreate(BaseModel):
    task_id: int
    customer_id: str
    tasker_id: str

# Routes
@app.get("/")
def read_root():
    return {"message": "Backend running", "status": "success"}

@app.post("/register/customer")
def register_customer(data: CustomerRegister):
    try:
        # Check if user already exists
        existing_user = next((u for u in mock_data["users"] if u["email"] == data.email), None)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        new_user = {
            "id": f"user{len(mock_data['users']) + 1}",
            "email": data.email,
            "password": data.password,
            "name": data.name
        }
        mock_data["users"].append(new_user)
        
        return {
            "message": "Customer registered successfully",
            "user_id": new_user["id"],
            "email": new_user["email"],
            "name": new_user["name"]
        }
        
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/login/customer")
def login_customer(data: CustomerLogin):
    try:
        # Find user in mock data
        user = next((u for u in mock_data["users"] if u["email"] == data.email and u["password"] == data.password), None)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "message": "Login successful",
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "user_name": user["name"],  # For compatibility
            "role": "customer"
        }
        
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/tasks")
def create_task(data: TaskCreate):
    try:
        # Create new task in mock data
        new_task = {
            "id": len(mock_data["tasks"]) + 1,
            "title": data.title,
            "description": data.description,
            "customer_id": data.customer_id,
            "status": data.status,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_data["tasks"].append(new_task)
        
        return {"message": "Task created", "task": new_task}
        
    except Exception as e:
        print(f"Task creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@app.get("/taskers")
def get_taskers():
    try:
        return {"taskers": mock_data["taskers"]}
        
    except Exception as e:
        print(f"Taskers fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch taskers: {str(e)}")

@app.post("/bookings")
def create_booking(data: BookingCreate):
    try:
        # Create new booking in mock data
        new_booking = {
            "id": len(mock_data["bookings"]) + 1,
            "task_id": data.task_id,
            "customer_id": data.customer_id,
            "tasker_id": data.tasker_id,
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_data["bookings"].append(new_booking)
        
        return {"message": "Booking created", "booking": [new_booking]}
        
    except Exception as e:
        print(f"Booking creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Booking creation failed: {str(e)}")

@app.get("/bookings")
def get_bookings(customer_id: str):
    try:
        # Filter bookings by customer_id
        customer_bookings = [b for b in mock_data["bookings"] if b["customer_id"] == customer_id]
        
        # Add task and tasker info
        for booking in customer_bookings:
            task = next((t for t in mock_data["tasks"] if t["id"] == booking["task_id"]), None)
            tasker = next((t for t in mock_data["taskers"] if t["id"] == booking["tasker_id"]), None)
            
            booking["task"] = {"title": task["title"]} if task else {"title": "Unknown Task"}
            booking["tasker"] = {"name": tasker["name"]} if tasker else {"name": "Unknown Tasker"}
        
        return {"bookings": customer_bookings}
        
    except Exception as e:
        print(f"Bookings fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch bookings: {str(e)}")

# Export for Vercel
handler = app