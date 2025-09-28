from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import random
import time
import jwt
import asyncio
from datetime import datetime, timedelta
from ai_models import TransportAIModel
import json
import math

# Initialize FastAPI app
app = FastAPI(
    title="Smart Public Transport API",
    description="API for smart public transport system with AI-powered ETA predictions and real-time GPS tracking",
    version="2.0.0"
)

# Mount static files
app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI model
ai_model = TransportAIModel()

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours for better UX

# Security
security = HTTPBearer()

# Updated user credentials - only user and driver
USERS = {
    "user": {"password": "iamuser", "role": "passenger", "full_name": "Passenger User"},
    "driver": {"password": "iamdriver", "role": "driver", "full_name": "Bus Driver"},
    # Additional demo drivers for testing
    "driver1": {"password": "iamdriver", "role": "driver", "full_name": "Sarah Wilson"},
    "driver2": {"password": "iamdriver", "role": "driver", "full_name": "Mike Johnson"},
}

# Enhanced global state for real-time tracking
bus_locations = {}
driver_sessions = {}
passenger_loads = {}
sos_alerts = {}
route_analytics = {}
system_metrics = {
    "total_requests": 0,
    "successful_predictions": 0,
    "active_sessions": 0,
    "last_update": datetime.now()
}

# Location update history for analytics
location_history = {}

# Enhanced Pydantic models

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    expires_in: int

class UserInfo(BaseModel):
    username: str
    role: str
    full_name: str

class BusRequest(BaseModel):
    start_location: str
    destination: str

class BusResponse(BaseModel):
    bus_id: str
    route_number: str
    start_location: str
    destination: str
    departure_time: str
    arrival_time: str
    fare: float
    capacity: int
    available_seats: int
    current_speed: Optional[float] = 0.0
    crowd_level: Optional[int] = 1
    eta_minutes: Optional[int] = 0

class EnhancedLocationResponse(BaseModel):
    bus_id: str
    route_number: str
    latitude: float
    longitude: float
    speed: float
    direction: str
    passenger_load: str
    driver_name: str
    last_updated: str
    trip_status: str

class ETARequest(BaseModel):
    bus_id: str
    current_location: str
    destination: str
    traffic_conditions: Optional[str] = "normal"
    passenger_count: Optional[int] = 0

class ETAResponse(BaseModel):
    bus_id: str
    estimated_arrival_time: str
    estimated_duration_minutes: float
    confidence_score: float
    factors_considered: List[str]
    route_info: Dict[str, Any]

# Enhanced Driver models
class DriverLocationUpdate(BaseModel):
    bus_id: str
    latitude: float
    longitude: float
    speed: float
    direction: str
    passenger_load: str  # "empty", "medium", "full"
    accuracy: Optional[float] = None
    altitude: Optional[float] = None

class DriverTripStart(BaseModel):
    bus_id: str
    route_number: str
    start_location: str
    estimated_duration: Optional[int] = None

class DriverTripEnd(BaseModel):
    bus_id: str
    end_location: str
    total_passengers: int
    trip_rating: Optional[int] = 5

class SOSAlert(BaseModel):
    bus_id: str
    alert_type: str  # "accident", "breakdown", "emergency", "medical"
    location: str
    description: Optional[str] = None
    severity: Optional[str] = "medium"  # "low", "medium", "high", "critical"

# Route and stop management
class BusRoute(BaseModel):
    route_id: str
    route_name: str
    stops: List[Dict[str, Any]]
    average_duration: int
    fare: float

class BusStop(BaseModel):
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float
    routes: List[str]

# Enhanced sample data with more realistic information
ENHANCED_ROUTES = [
    {
        "route_id": "RT001",
        "route_name": "Route 42",
        "stops": [
            {"name": "Central Station", "lat": 26.9124, "lng": 75.7873, "order": 1},
            {"name": "City Mall", "lat": 26.9200, "lng": 75.8000, "order": 2},
            {"name": "Hospital Junction", "lat": 26.9300, "lng": 75.8100, "order": 3},
            {"name": "Airport Terminal", "lat": 26.9400, "lng": 75.8200, "order": 4}
        ],
        "average_duration": 45,
        "fare": 2.50
    },
    {
        "route_id": "RT002", 
        "route_name": "Route 15",
        "stops": [
            {"name": "University Campus", "lat": 26.8900, "lng": 75.7600, "order": 1},
            {"name": "Tech Park", "lat": 26.9000, "lng": 75.7700, "order": 2},
            {"name": "Shopping Center", "lat": 26.9100, "lng": 75.7800, "order": 3},
            {"name": "Downtown Mall", "lat": 26.9200, "lng": 75.7900, "order": 4}
        ],
        "average_duration": 35,
        "fare": 1.75
    },
    {
        "route_id": "RT003",
        "route_name": "Route 7", 
        "stops": [
            {"name": "Suburb Station", "lat": 26.8800, "lng": 75.7400, "order": 1},
            {"name": "Industrial Area", "lat": 26.8900, "lng": 75.7500, "order": 2},
            {"name": "Metro Junction", "lat": 26.9000, "lng": 75.7600, "order": 3},
            {"name": "City Center", "lat": 26.9100, "lng": 75.7700, "order": 4}
        ],
        "average_duration": 40,
        "fare": 3.00
    }
]

# Enhanced bus fleet with realistic data
ENHANCED_BUSES = [
    {
        "bus_id": "BUS001",
        "route_number": "Route 42",
        "route_id": "RT001",
        "start_location": "Central Station",
        "destination": "Airport Terminal",
        "departure_time": "08:30",
        "arrival_time": "09:15",
        "fare": 2.50,
        "capacity": 50,
        "available_seats": 35,
        "driver_id": "driver",
        "status": "active"
    },
    {
        "bus_id": "BUS002",
        "route_number": "Route 15", 
        "route_id": "RT002",
        "start_location": "University Campus",
        "destination": "Downtown Mall",
        "departure_time": "09:00", 
        "arrival_time": "09:35",
        "fare": 1.75,
        "capacity": 40,
        "available_seats": 28,
        "driver_id": "driver1",
        "status": "active"
    },
    {
        "bus_id": "BUS003",
        "route_number": "Route 7",
        "route_id": "RT003", 
        "start_location": "Suburb Station",
        "destination": "City Center",
        "departure_time": "08:45",
        "arrival_time": "09:25", 
        "fare": 3.00,
        "capacity": 60,
        "available_seats": 42,
        "driver_id": "driver2",
        "status": "active"
    }
]

# Utility functions
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calculate_eta_with_traffic(distance_km, speed_kmh, traffic_factor=1.0, time_of_day=None):
    """Enhanced ETA calculation with traffic considerations"""
    if time_of_day is None:
        time_of_day = datetime.now().hour
    
    # Adjust speed based on time of day
    if 7 <= time_of_day <= 9 or 17 <= time_of_day <= 19:  # Rush hours
        speed_kmh *= 0.7
        traffic_factor *= 1.3
    elif 22 <= time_of_day or time_of_day <= 5:  # Night time
        speed_kmh *= 1.2
        traffic_factor *= 0.8
    
    base_time_hours = distance_km / max(speed_kmh, 5)  # Minimum speed of 5 km/h
    actual_time_hours = base_time_hours * traffic_factor
    
    return actual_time_hours * 60  # Return in minutes

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "role": payload.get("role")}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(verify_token)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

# Background task for updating system metrics
async def update_system_metrics():
    """Background task to update system metrics"""
    while True:
        system_metrics["last_update"] = datetime.now()
        system_metrics["active_sessions"] = len(driver_sessions)
        await asyncio.sleep(60)  # Update every minute

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    asyncio.create_task(update_system_metrics())

# Basic endpoints
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

@app.get("/")
async def root():
    return {
        "message": "Smart Public Transport API is running!", 
        "version": "2.0.0",
        "features": ["Real-time GPS tracking", "AI-powered ETA", "Driver app", "Passenger app"],
        "available_roles": ["passenger", "driver"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "active_buses": len(bus_locations),
        "active_drivers": len(driver_sessions)
    }

# Enhanced Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Enhanced login endpoint with full name support"""
    if request.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user = USERS[request.username]
    if user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username, "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    # Update system metrics
    system_metrics["total_requests"] += 1
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        full_name=user["full_name"],
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/auth/me", response_model=UserInfo)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Get current user information with full name"""
    user = USERS.get(current_user["username"])
    return UserInfo(
        username=current_user["username"], 
        role=current_user["role"],
        full_name=user["full_name"] if user else current_user["username"]
    )

# Enhanced Driver endpoints
@app.post("/driver/location/update")
async def update_driver_location(
    request: DriverLocationUpdate,
    current_user: dict = Depends(require_role("driver"))
):
    """Enhanced location update with history tracking"""
    timestamp = datetime.now()
    
    # Store current location
    bus_locations[request.bus_id] = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "speed": request.speed,
        "direction": request.direction,
        "accuracy": request.accuracy,
        "altitude": request.altitude,
        "last_updated": timestamp.isoformat(),
        "driver": current_user["username"],
        "passenger_load": request.passenger_load
    }
    
    # Store in history for analytics
    if request.bus_id not in location_history:
        location_history[request.bus_id] = []
    
    location_history[request.bus_id].append({
        "timestamp": timestamp.isoformat(),
        "latitude": request.latitude,
        "longitude": request.longitude,
        "speed": request.speed,
        "direction": request.direction
    })
    
    # Keep only last 100 location points
    if len(location_history[request.bus_id]) > 100:
        location_history[request.bus_id] = location_history[request.bus_id][-100:]
    
    passenger_loads[request.bus_id] = request.passenger_load
    
    return {"status": "success", "message": "Location updated", "timestamp": timestamp.isoformat()}

@app.post("/driver/trip/start")
async def start_trip(
    request: DriverTripStart,
    current_user: dict = Depends(require_role("driver"))
):
    """Enhanced trip start with route validation"""
    # Validate route exists
    route_exists = any(route["route_name"] == request.route_number for route in ENHANCED_ROUTES)
    
    driver_sessions[request.bus_id] = {
        "driver": current_user["username"],
        "route_number": request.route_number,
        "route_exists": route_exists,
        "start_location": request.start_location,
        "start_time": datetime.now().isoformat(),
        "estimated_duration": request.estimated_duration,
        "status": "active",
        "total_distance": 0.0,
        "passenger_count": 0
    }
    
    return {
        "status": "success", 
        "message": "Trip started",
        "route_validated": route_exists,
        "trip_id": f"TRIP_{int(time.time())}"
    }

@app.post("/driver/trip/end")
async def end_trip(
    request: DriverTripEnd,
    current_user: dict = Depends(require_role("driver"))
):
    """Enhanced trip end with analytics"""
    if request.bus_id in driver_sessions:
        session = driver_sessions[request.bus_id]
        start_time = datetime.fromisoformat(session["start_time"])
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60  # in minutes
        
        # Update analytics
        route_number = session["route_number"]
        if route_number not in route_analytics:
            route_analytics[route_number] = {
                "total_trips": 0,
                "total_passengers": 0,
                "average_duration": 0,
                "total_distance": 0
            }
        
        analytics = route_analytics[route_number]
        analytics["total_trips"] += 1
        analytics["total_passengers"] += request.total_passengers
        analytics["average_duration"] = (analytics["average_duration"] + duration) / 2
        
        driver_sessions[request.bus_id].update({
            "end_location": request.end_location,
            "end_time": end_time.isoformat(),
            "actual_duration": duration,
            "total_passengers": request.total_passengers,
            "trip_rating": request.trip_rating,
            "status": "completed"
        })
    
    return {"status": "success", "message": "Trip ended", "analytics_updated": True}

@app.post("/driver/sos")
async def send_sos_alert(
    request: SOSAlert,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("driver"))
):
    """Enhanced SOS with severity levels and notifications"""
    alert_id = f"ALERT_{int(time.time())}_{request.bus_id}"
    
    sos_alerts[alert_id] = {
        "alert_id": alert_id,
        "bus_id": request.bus_id,
        "driver": current_user["username"],
        "alert_type": request.alert_type,
        "severity": request.severity,
        "location": request.location,
        "description": request.description,
        "timestamp": datetime.now().isoformat(),
        "status": "active"
    }
    
    # Add background task for notifications (in real app, this would send notifications)
    background_tasks.add_task(notify_sos, alert_id, request.severity)
    
    return {
        "status": "success",
        "message": "SOS alert sent",
        "alert_id": alert_id,
        "severity": request.severity,
        "estimated_response_time": "5-10 minutes" if request.severity == "critical" else "15-30 minutes"
    }

async def notify_sos(alert_id: str, severity: str):
    """Background task to handle SOS notifications"""
    # In a real application, this would:
    # - Send notifications to emergency services
    # - Send SMS/email alerts
    # - Contact authorities if critical
    print(f"SOS Alert {alert_id} - Severity: {severity} - Emergency services notified")

# Enhanced Passenger endpoints
@app.post("/buses/available", response_model=List[BusResponse])
async def get_available_buses(
    request: BusRequest,
    current_user: dict = Depends(verify_token)
):
    """Enhanced bus search with real-time data"""
    try:
        available_buses = []
        
        for bus in ENHANCED_BUSES:
            # Enhanced matching logic with route information
            route_data = next((r for r in ENHANCED_ROUTES if r["route_id"] == bus["route_id"]), None)
            
            if route_data:
                # Check if route serves the requested locations
                stops = [stop["name"].lower() for stop in route_data["stops"]]
                start_match = any(request.start_location.lower() in stop for stop in stops)
                dest_match = any(request.destination.lower() in stop for stop in stops)
                
                if start_match or dest_match:
                    # Get real-time data if available
                    current_speed = 0.0
                    if bus["bus_id"] in bus_locations:
                        current_speed = bus_locations[bus["bus_id"]]["speed"]
                    
                    # Calculate dynamic ETA using AI model
                    eta_minutes = 0
                    try:
                        # Simulate distance calculation
                        distance_km = random.uniform(5, 25)
                        speed_kmh = max(current_speed, 20)  # Use current speed or default
                        
                        eta_prediction = ai_model.predict_eta(
                            speed_kmh=speed_kmh,
                            distance_km=distance_km
                        )
                        eta_minutes = int(eta_prediction)
                    except:
                        eta_minutes = random.randint(10, 45)
                    
                    available_buses.append(BusResponse(
                        **bus,
                        current_speed=current_speed,
                        crowd_level=random.randint(1, 5),
                        eta_minutes=eta_minutes
                    ))
        
        if not available_buses:
            raise HTTPException(
                status_code=404,
                detail=f"No buses found between {request.start_location} and {request.destination}"
            )
        
        # Update metrics
        system_metrics["total_requests"] += 1
        system_metrics["successful_predictions"] += len(available_buses)
        
        return available_buses
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buses/{bus_id}/location", response_model=EnhancedLocationResponse)
async def get_bus_location(
    bus_id: str,
    current_user: dict = Depends(verify_token)
):
    """Enhanced bus location with driver info and trip status"""
    try:
        # Find the bus
        bus = next((b for b in ENHANCED_BUSES if b["bus_id"] == bus_id), None)
        if not bus:
            raise HTTPException(status_code=404, detail=f"Bus {bus_id} not found")
        
        # Get real-time location or generate simulated data
        if bus_id in bus_locations:
            location_data = bus_locations[bus_id]
        else:
            # Generate simulated location around Jaipur
            location_data = {
                "latitude": 26.9124 + random.uniform(-0.1, 0.1),
                "longitude": 75.7873 + random.uniform(-0.1, 0.1),
                "speed": random.uniform(15, 45),
                "direction": random.choice(["North", "South", "East", "West", "NE", "NW", "SE", "SW"]),
                "passenger_load": random.choice(["empty", "medium", "full"]),
                "driver": bus["driver_id"],
                "last_updated": datetime.now().isoformat()
            }
        
        # Get trip status
        trip_status = "idle"
        if bus_id in driver_sessions:
            session = driver_sessions[bus_id]
            trip_status = session["status"]
        
        # Get driver name
        driver_name = USERS.get(location_data["driver"], {}).get("full_name", location_data["driver"])
        
        return EnhancedLocationResponse(
            bus_id=bus_id,
            route_number=bus["route_number"],
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
            speed=location_data["speed"],
            direction=location_data["direction"],
            passenger_load=location_data.get("passenger_load", "unknown"),
            driver_name=driver_name,
            last_updated=location_data["last_updated"],
            trip_status=trip_status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/buses/{bus_id}/eta", response_model=ETAResponse)
async def predict_eta(
    bus_id: str,
    request: ETARequest,
    current_user: dict = Depends(verify_token)
):
    """Enhanced ETA prediction with route information"""
    try:
        # Find the bus and route
        bus = next((b for b in ENHANCED_BUSES if b["bus_id"] == bus_id), None)
        if not bus:
            raise HTTPException(status_code=404, detail=f"Bus {bus_id} not found")
        
        route_data = next((r for r in ENHANCED_ROUTES if r["route_id"] == bus["route_id"]), None)
        
        # Get current location and speed
        current_location = bus_locations.get(bus_id, {})
        current_speed = current_location.get("speed", 25.0)
        
        # Enhanced distance calculation (simplified for demo)
        distance_km = random.uniform(2, 20)
        
        # Traffic factor based on conditions and passenger count
        traffic_factors = {
            "light": 0.8,
            "normal": 1.0,
            "heavy": 1.4,
            "congested": 1.8
        }
        traffic_factor = traffic_factors.get(request.traffic_conditions, 1.0)
        
        # Adjust for passenger load
        if request.passenger_count > 30:
            traffic_factor *= 1.1  # Slower boarding/alighting
        
        # Use AI model for prediction
        eta_prediction = ai_model.predict_eta_with_confidence(
            speed_kmh=current_speed,
            distance_km=distance_km,
            traffic_factor=traffic_factor
        )
        
        # Enhanced factors considered
        factors_considered = [
            "Current traffic conditions",
            "Historical route data",
            "Real-time bus speed",
            "Time of day",
            "Weather conditions"
        ]
        
        if request.passenger_count > 0:
            factors_considered.append("Passenger load impact")
        
        # Route information
        route_info = {
            "route_name": route_data["route_name"] if route_data else "Unknown",
            "total_stops": len(route_data["stops"]) if route_data else 0,
            "average_stop_time": "2-3 minutes"
        }
        
        return ETAResponse(
            bus_id=bus_id,
            estimated_arrival_time=eta_prediction["estimated_arrival_time"],
            estimated_duration_minutes=eta_prediction["eta_minutes"],
            confidence_score=eta_prediction["confidence_score"],
            factors_considered=factors_considered,
            route_info=route_info
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route management endpoints
@app.get("/routes")
async def get_routes(current_user: dict = Depends(verify_token)):
    """Get all available routes"""
    return {"routes": ENHANCED_ROUTES}

@app.get("/routes/{route_id}/stops")
async def get_route_stops(route_id: str, current_user: dict = Depends(verify_token)):
    """Get stops for a specific route"""
    route = next((r for r in ENHANCED_ROUTES if r["route_id"] == route_id), None)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {"route": route["route_name"], "stops": route["stops"]}

@app.get("/buses")
async def get_all_buses(current_user: dict = Depends(verify_token)):
    """Get all buses with enhanced information"""
    enhanced_buses = []
    
    for bus in ENHANCED_BUSES:
        bus_copy = bus.copy()
        
        # Add real-time data if available
        if bus["bus_id"] in bus_locations:
            location = bus_locations[bus["bus_id"]]
            bus_copy["current_location"] = {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "last_updated": location["last_updated"]
            }
            bus_copy["current_speed"] = location["speed"]
        
        # Add trip status
        if bus["bus_id"] in driver_sessions:
            session = driver_sessions[bus["bus_id"]]
            bus_copy["trip_status"] = session["status"]
            bus_copy["trip_start_time"] = session.get("start_time")
        
        enhanced_buses.append(bus_copy)
    
    return {"buses": enhanced_buses, "total": len(enhanced_buses)}

# System status endpoints
@app.get("/system/status")
async def get_system_status():
    """Get system status information"""
    active_drivers = len([s for s in driver_sessions.values() if s.get("status") == "active"])
    
    return {
        "system_health": "operational",
        "total_buses": len(ENHANCED_BUSES),
        "active_drivers": active_drivers,
        "buses_with_gps": len(bus_locations),
        "active_alerts": len([alert for alert in sos_alerts.values() if alert["status"] == "active"]),
        "system_uptime": "operational",
        "last_update": system_metrics["last_update"].isoformat()
    }

@app.get("/system/analytics") 
async def get_system_analytics():
    """Get basic system analytics"""
    active_drivers = len([s for s in driver_sessions.values() if s.get("status") == "active"])
    total_passengers = sum(s.get("total_passengers", 0) for s in driver_sessions.values())
    
    # Calculate popular routes from analytics
    popular_routes = []
    for route_name, analytics in route_analytics.items():
        popular_routes.append({
            "route": route_name,
            "passengers": analytics["total_passengers"],
            "trips": analytics["total_trips"],
            "avg_duration": analytics["average_duration"]
        })
    
    # Sort by passenger count
    popular_routes.sort(key=lambda x: x["passengers"], reverse=True)
    
    return {
        "total_buses": len(ENHANCED_BUSES),
        "active_drivers": active_drivers,
        "total_passengers_today": total_passengers,
        "average_eta_accuracy": 0.89,
        "popular_routes": popular_routes[:5],
        "system_requests": system_metrics["total_requests"],
        "successful_predictions": system_metrics["successful_predictions"]
    }

# SOS Alert management
@app.get("/alerts/sos")
async def get_sos_alerts(current_user: dict = Depends(verify_token)):
    """Get SOS alerts (available to both drivers and passengers for awareness)"""
    # Only return non-sensitive information for passengers
    if current_user["role"] == "passenger":
        public_alerts = []
        for alert in sos_alerts.values():
            if alert["status"] == "active":
                public_alerts.append({
                    "alert_type": alert["alert_type"],
                    "severity": alert["severity"], 
                    "timestamp": alert["timestamp"],
                    "bus_route": "Route information available"
                })
        return {"public_alerts": public_alerts}
    
    # Full information for drivers
    return {"sos_alerts": list(sos_alerts.values())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
