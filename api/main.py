from fastapi import FastAPI, HTTPException, Path, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from supabase import create_client
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from ai_integration import classify_service_request, get_service_followups, match_providers
# from uber_like_booking_system import UberLikeBookingSystem

load_dotenv()
app = FastAPI(
    title="Woke AI Platform",
    description="Premium in-house services with AI-powered matching"
)

# --------------------------
# CORS Middleware
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Static Files (for Vercel)
# --------------------------
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# --------------------------
# Supabase client
# --------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Uber-like booking system (temporarily disabled)
# booking_system = UberLikeBookingSystem()

# --------------------------
# Schemas
# --------------------------
class CustomerRegister(BaseModel):
    email: str
    password: str
    name: str

class TaskerRegister(BaseModel):
    email: str
    password: str
    name: str
    skills: list[str]
    hourly_rate: float
    bio: str

class ProviderRegister(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    skills: list[str]
    hourly_rate: float
    bio: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    customer_id: str
    status: Optional[str] = "open"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # open, in-progress, completed

class BookingCreate(BaseModel):
    task_id: int
    tasker_id: str
    customer_id: str

class BookingUpdate(BaseModel):
    status: str  # accepted, declined, completed

class ReviewCreate(BaseModel):
    booking_id: int
    customer_id: str
    tasker_id: str
    rating: int
    review_text: Optional[str] = None # matches your table column

# --------------------------
# Root
# --------------------------
@app.get("/")
def root():
    return {"message": "Backend running"}

@app.get("/profiles")
def get_profiles():
    response = supabase.table("profiles").select("*").execute()
    return response.data

# --------------------------
# Login Endpoint
# --------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login/customer")
def login_customer(email: str = Body(...), password: str = Body(...)):
    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if not user.user:
        raise HTTPException(status_code=400, detail="Login failed")
    
    # Get user profile to return name
    try:
        profile_response = supabase.table("profiles").select("name").eq("id", user.user.id).execute()
        user_name = profile_response.data[0]["name"] if profile_response.data else "User"
    except:
        user_name = "User"
    
    return {"message": "Login successful", "user_id": user.user.id, "user_name": user_name}

# --------------------------
# Step 2: Providers Endpoint
# --------------------------
@app.get("/providers")
def get_providers(service: str = Query(..., description="Service type, e.g., cleaning, repairs, carcare, beauty, appliance")):
    """
    Fetch providers filtered by service type.
    """
    try:
        # Assuming your Supabase table for providers is 'providers' 
        # and each provider has a 'service_type' column like 'cleaning', 'repairs', etc.
        response = supabase.table("providers").select("*").eq("service_type", service).execute()
        if response.data is None:
            return []
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch providers: {str(e)}")

# --------------------------
# Registration Endpoints
# --------------------------
@app.post("/register/customer")
def register_customer(data: CustomerRegister):
    user = supabase.auth.sign_up({"email": data.email, "password": data.password})
    if not user.user:
        raise HTTPException(status_code=400, detail=user.get("message", "Signup failed"))

    supabase.table("profiles").insert({
        "id": user.user.id,
        "name": data.name,
        "role": "customer"
    }).execute()
    return {"message": "Customer registered", "user_id": user.user.id}

@app.post("/register/tasker")
def register_tasker(data: TaskerRegister):
    user = supabase.auth.sign_up({"email": data.email, "password": data.password})
    if not user.user:
        raise HTTPException(status_code=400, detail=user.get("message", "Signup failed"))

    supabase.table("profiles").insert({
        "id": user.user.id,
        "name": data.name,
        "role": "tasker",
        "skills": data.skills,
        "hourly_rate": data.hourly_rate,
        "bio": data.bio
    }).execute()
    return {"message": "Tasker registered", "tasker_id": user.user.id}

# --------------------------
# Tasks Endpoints
# --------------------------
@app.post("/tasks")
def create_task(data: TaskCreate):
    response = supabase.table("tasks").insert({
        "title": data.title,
        "description": data.description,
        "customer_id": data.customer_id,
        "status": data.status
    }).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create task")
    return {"message": "Task created", "task": response.data}

@app.get("/tasks")
def list_tasks(customer_id: str):
    response = supabase.table("tasks").select("*").eq("customer_id", customer_id).execute()
    return {"tasks": response.data}

@app.patch("/tasks/{task_id}")
def update_task(task_id: int = Path(...), data: TaskUpdate = None):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Task not found or update failed")
    return {"message": "Task updated", "task": response.data}

# --------------------------
# Bookings Endpoints
# --------------------------
@app.post("/bookings")
def create_booking(data: BookingCreate):
    response = supabase.table("bookings").insert({
        "task_id": data.task_id,
        "customer_id": data.customer_id,
        "tasker_id": data.tasker_id,
        "status": "pending"
    }).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create booking")
    return {"message": "Booking created", "booking": response.data}


@app.get("/bookings/tasker")
def list_tasker_bookings(tasker_id: str):
    response = supabase.table("bookings").select("*").eq("tasker_id", tasker_id).execute()
    return {"bookings": response.data}

@app.get("/taskers")
def get_taskers():
    """Get all available taskers"""
    try:
        response = supabase.table("profiles").select("id, name, skills, hourly_rate, bio").eq("role", "tasker").execute()
        return {"taskers": response.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch taskers: {str(e)}")

@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str):
    """Get user profile by ID"""
    try:
        response = supabase.table("profiles").select("*").eq("id", profile_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    hourly_rate: Optional[float] = None
    skills: Optional[list[str]] = None
    bio: Optional[str] = None
    availability: Optional[str] = None

@app.patch("/profiles/{profile_id}")
def update_profile(profile_id: str, data: ProfileUpdate):
    """Update user profile"""
    try:
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.hourly_rate is not None:
            update_data["hourly_rate"] = data.hourly_rate
        if data.skills is not None:
            update_data["skills"] = data.skills
        if data.bio is not None:
            update_data["bio"] = data.bio
        if data.availability is not None:
            update_data["availability"] = data.availability
        # Note: phone and address are stored in localStorage on frontend
            
        response = supabase.table("profiles").update(update_data).eq("id", profile_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Profile updated successfully", "profile": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@app.patch("/bookings/{booking_id}")
def update_booking(booking_id: int, data: BookingUpdate):
    response = supabase.table("bookings").update({"status": data.status}).eq("id", booking_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Booking not found or update failed")
    return {"message": f"Booking updated to {data.status}", "booking": response.data}

@app.patch("/bookings/{booking_id}/customer")
def update_booking_customer(booking_id: int, customer_id: str):
    """Update customer_id for a booking (for fixing data issues)"""
    response = supabase.table("bookings").update({"customer_id": customer_id}).eq("id", booking_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking customer updated", "booking": response.data[0]}

# --------------------------
# Reviews Endpoints
# --------------------------
@app.post("/reviews")
def create_review(data: ReviewCreate):
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    try:
        response = supabase.table("reviews").insert({
            "booking_id": data.booking_id,
            "customer_id": data.customer_id,
            "tasker_id": data.tasker_id,
            "rating": data.rating,
            "review_text": data.review_text
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review: {str(e)}")
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create review")
    return {"message": "Review submitted", "review": response.data}

@app.get("/reviews/{tasker_id}")
def list_tasker_reviews(tasker_id: str):
    try:
        response = supabase.table("reviews").select("*").eq("tasker_id", tasker_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reviews: {str(e)}")
    if response.data is None:
        return {"reviews": []}
    return {"reviews": response.data}

# --------------------------
# AI Integration Endpoints
# --------------------------
class ClassifyRequest(BaseModel):
    text: str

class FollowupRequest(BaseModel):
    service_id: str
    answers: Dict[str, Any] = {}

class MatchRequest(BaseModel):
    service_id: str
    spec: Dict[str, Any] = {}
    location: Optional[Dict[str, float]] = None

@app.post("/api/ai/classify")
def classify_service(data: ClassifyRequest):
    try:
        result = classify_service_request(data.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/api/ai/followups")
def get_service_followups_endpoint(data: FollowupRequest):
    try:
        result = get_service_followups(data.service_id, data.answers)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Followup generation failed: {str(e)}")

@app.post("/api/ai/match")
def match_service_providers(data: MatchRequest):
    try:
        result = match_providers(data.service_id, data.spec, data.location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider matching failed: {str(e)}")

@app.get("/api/ai/health")
def ai_health_check():
    return {"status": "healthy", "ai_enabled": True, "ollama_url": "http://localhost:11434"}

@app.post("/checkout")
async def checkout(booking: dict):
    """
    Mock checkout endpoint.
    Pretend we create a payment session and return a fake paywall URL.
    """
    booking_id = booking.get("booking_id")
    if not booking_id:
        raise HTTPException(status_code=400, detail="Missing booking_id")

    # In real case: create Stripe/PayPal session here
    payment_url = f"http://127.0.0.1:8000/pay/{booking_id}"

    return {"status": "pending_payment", "payment_url": payment_url}

@app.get("/pay/{booking_id}", response_class=HTMLResponse)
async def pay_page(booking_id: str):
    return f"""
    <html>
      <head>
        <title>Mock Payment</title>
      </head>
      <body style="font-family: sans-serif; text-align: center; margin-top: 100px;">
        <h1>Payment for Booking {booking_id}</h1>
        <p>This is a mock paywall. Click below to simulate payment.</p>
        <form action="/pay/success/{booking_id}" method="get">
          <button type="submit" style="padding: 10px 20px; font-size: 16px;">Pay Now</button>
        </form>
      </body>
    </html>
    """

@app.get("/pay/success/{booking_id}", response_class=HTMLResponse)
async def pay_success(booking_id: str):
    return f"""
    <html>
      <head>
        <title>Payment Success</title>
      </head>
      <body style="font-family: sans-serif; text-align: center; margin-top: 100px;">
        <h1>Payment Successful</h1>
        <p>Your payment for booking {booking_id} has been processed.</p>
        <p>Thank you for using our service!</p>
      </body>
    </html>
    """

# --------------------------
# Provider Authentication
# --------------------------

@app.post("/register/provider")
def register_provider(provider: ProviderRegister):
    try:
        # Create auth user
        user = supabase.auth.sign_up({
            "email": provider.email,
            "password": provider.password
        })
        
        if not user.user:
            raise HTTPException(status_code=400, detail="Registration failed")
        
        # Create provider profile
        profile_data = {
            "id": user.user.id,
            "name": provider.name,
            "role": "tasker",
            "skills": provider.skills,
            "hourly_rate": provider.hourly_rate,
            "bio": provider.bio
        }
        
        result = supabase.table("profiles").insert(profile_data).execute()
        
        return {"message": "Provider registered successfully", "provider_id": user.user.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/login/provider")
def login_provider(email: str = Body(...), password: str = Body(...)):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if not user.user:
            raise HTTPException(status_code=400, detail="Login failed")
        
        # Get provider profile
        profile_response = supabase.table("profiles").select("name").eq("id", user.user.id).execute()
        provider_name = profile_response.data[0]["name"] if profile_response.data else "Provider"
        
        return {"message": "Login successful", "provider_id": user.user.id, "provider_name": provider_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/bookings")
def get_bookings(customer_id: str = Query(None), provider_id: str = Query(None)):
    """Get bookings - simplified for performance"""
    try:
        if customer_id:
            # Get bookings for a specific customer
            response = supabase.table("bookings") \
                .select("id, task_id, customer_id, status, created_at, task:tasks(title), tasker:profiles!bookings_tasker_id_fkey(name)") \
                .execute()
            
            all_bookings = response.data or []
            customer_bookings = [booking for booking in all_bookings if booking.get("customer_id") == customer_id]
            
            return {"bookings": customer_bookings}
        elif provider_id:
            # Get bookings for a specific provider
            response = supabase.table("bookings") \
                .select("id, task_id, customer_id, status, created_at, task:tasks(title)") \
                .eq("tasker_id", provider_id) \
                .execute()
            
            return {"bookings": response.data or []}
        else:
            raise HTTPException(status_code=400, detail="Either customer_id or provider_id must be provided")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch bookings: {str(e)}")

@app.patch("/bookings/{booking_id}")
def update_booking(booking_id: str, status: str = Body(...)):
    """Update booking status - simplified for performance with Uber-like support"""
    try:
        # Handle 'cancelled' status by mapping to 'completed' in database
        # but track the real status in a separate field or localStorage
        db_status = status
        if status == "cancelled":
            db_status = "completed"  # Map cancelled to completed for database constraint
        
        response = supabase.table("bookings") \
            .update({"status": db_status}) \
            .eq("id", booking_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Return the original status for frontend
        booking = response.data[0]
        booking["status"] = status  # Return original status
        
        return {"message": "Booking updated successfully", "booking": booking}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update booking: {str(e)}")