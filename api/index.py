from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
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

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://civjbgjrknhaknietyth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_secret_HEvjYo69xYMQ6dfBDKdz-A_sNx3CAKQ")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client created successfully")
except Exception as e:
    print(f"Error creating Supabase client: {e}")
    supabase = None

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
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Create user in Supabase Auth
        user = supabase.auth.sign_up({"email": data.email, "password": data.password})
        
        if not user.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Create profile
        profile_data = {
            "id": user.user.id,
            "name": data.name,
            "role": "customer"
        }
        
        profile_response = supabase.table("profiles").insert(profile_data).execute()
        
        if not profile_response.data:
            raise HTTPException(status_code=400, detail="Failed to create profile")
        
        return {
            "message": "Customer registered successfully",
            "user_id": user.user.id,
            "email": user.user.email
        }
        
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/login/customer")
def login_customer(data: CustomerLogin):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Login user
        user = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})
        
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Get profile
        profile_response = supabase.table("profiles").select("*").eq("id", user.user.id).execute()
        
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = profile_response.data[0]
        
        return {
            "message": "Login successful",
            "user_id": user.user.id,
            "email": user.user.email,
            "name": profile.get("name", ""),
            "role": profile.get("role", "customer")
        }
        
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/tasks")
def create_task(data: TaskCreate):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        response = supabase.table("tasks").insert({
            "title": data.title,
            "description": data.description,
            "customer_id": data.customer_id,
            "status": data.status
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create task")
        
        return {"message": "Task created", "task": response.data[0]}
        
    except Exception as e:
        print(f"Task creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@app.get("/taskers")
def get_taskers():
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        response = supabase.table("profiles").select("id,name,skills,hourly_rate,bio").eq("role", "tasker").execute()
        
        if not response.data:
            return {"taskers": []}
        
        return {"taskers": response.data}
        
    except Exception as e:
        print(f"Taskers fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch taskers: {str(e)}")

@app.post("/bookings")
def create_booking(data: BookingCreate):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        response = supabase.table("bookings").insert({
            "task_id": data.task_id,
            "customer_id": data.customer_id,
            "tasker_id": data.tasker_id,
            "status": "pending"
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create booking")
        
        return {"message": "Booking created", "booking": response.data[0]}
        
    except Exception as e:
        print(f"Booking creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Booking creation failed: {str(e)}")

@app.get("/bookings")
def get_bookings(customer_id: str):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        response = supabase.table("bookings").select(
            "id,task_id,customer_id,status,created_at,task:tasks(title),tasker:profiles!bookings_tasker_id_fkey(name)"
        ).eq("customer_id", customer_id).execute()
        
        if not response.data:
            return {"bookings": []}
        
        return {"bookings": response.data}
        
    except Exception as e:
        print(f"Bookings fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch bookings: {str(e)}")

# Export for Vercel
handler = app