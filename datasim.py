import random
from datetime import datetime, timedelta

# --- Route Metadata (Used by both Python and React) ---

ROUTE_METADATA = {
    "Route-1": {
        "name": "City Center to University Loop",
        "stops": [
            {"name": "Town Hall", "lat": 26.918, "lon": 75.790, "index": 0},
            {"name": "Main Market", "lat": 26.925, "lon": 75.795, "index": 1},
            {"name": "University Gate", "lat": 26.932, "lon": 75.785, "index": 2},
            {"name": "Hospital Square", "lat": 26.920, "lon": 75.778, "index": 3}
        ]
    },
    "Route-2": {
        "name": "Railway Station Shuttle",
        "stops": [
            {"name": "Railway Station", "lat": 26.910, "lon": 75.805, "index": 0},
            {"name": "Industrial Area", "lat": 26.900, "lon": 75.815, "index": 1},
            {"name": "Airport Road", "lat": 26.895, "lon": 75.800, "index": 2}
        ]
    }
}

# --- Operational State (Simulates persistent driver/admin input) ---
# Stores the current state (running, crowdedness, assigned route) for 15 buses.
BUS_OPERATIONAL_STATUS = {
    f"Bus-{i}": {
        "is_running": (i % 3 != 0), # Roughly 2/3 running
        "status_message": "On Route" if (i % 3 != 0) else "Off Duty",
        "crowdedness_level": random.choice(["LIGHT", "MODERATE", "HEAVY"]),
        "assigned_route_id": f"Route-{(i % 2) + 1}" # Assigns buses permanently to Route-1 or Route-2
    } for i in range(1, 16)
}

def get_routes_metadata():
    """Returns static route metadata."""
    return ROUTE_METADATA

def get_stops_in_order(route_id, start_name, end_name):
    """Calculates stops between A and B for journey time calculation."""
    route = ROUTE_METADATA.get(route_id)
    if not route:
        return []
    stops = route['stops']
    try:
        start_index = next(s['index'] for s in stops if s['name'] == start_name)
        end_index = next(s['index'] for s in stops if s['name'] == end_name)
    except StopIteration:
        return []
    
    # Ensure stops are correctly ordered for the journey (handling loops/reverse trips simply)
    start_point = min(start_index, end_index)
    end_point = max(start_index, end_index)
        
    return [s for s in stops if start_point < s['index'] <= end_point]

def generate_live_bus_status(num_buses=15):
    """
    Generates simulated real-time GPS and status data for the entire fleet.
    Incorporates persistent driver/admin state from BUS_OPERATIONAL_STATUS.
    """
    status = {}
    
    for i in range(1, num_buses + 1):
        bus_id = f"Bus-{i}"
        op_state = BUS_OPERATIONAL_STATUS.get(bus_id, {})
        
        # Determine the assigned route
        route_key = op_state.get("assigned_route_id", "Route-1")
        route_data = ROUTE_METADATA.get(route_key, ROUTE_METADATA["Route-1"])
        
        if not op_state.get("is_running", False):
            # Return static state for off-duty bus (low bandwidth friendly)
            status[bus_id] = {
                "bus_id": bus_id, "route_id": route_key, "is_running": False,
                "status_message": op_state.get("status_message", "Off Duty"),
                "crowdedness": op_state.get("crowdedness_level", "LIGHT"),
                "location": {"latitude": 0.0, "longitude": 0.0},
                "next_stop_name": "Depot", "passengers": 0, "speed_kmh": 0, "distance_to_stop_km": 0,
                "current_stop": "Depot"
            }
            continue

        # --- Simulation for Running Bus ---
        
        current_stop = random.choice(route_data['stops'])
        # Determine the next stop
        next_stop_list = [s for s in route_data['stops'] if s['name'] != current_stop['name']]
        next_stop = random.choice(next_stop_list) if next_stop_list else current_stop
        
        distance_to_stop_km = random.uniform(0.8, 4.5)
        
        # Simulate passengers based on crowdedness_level
        crowdedness_level = op_state["crowdedness_level"]
        passengers = {"LIGHT": random.randint(5, 20), "MODERATE": random.randint(30, 45), "HEAVY": random.randint(50, 60)}.get(crowdedness_level, 20)

        status[bus_id] = {
            "bus_id": bus_id,
            "route_id": route_key,
            "is_running": True,
            "status_message": op_state["status_message"],
            "current_stop": current_stop['name'],
            "next_stop_name": next_stop['name'],
            "next_stop_index": next_stop['index'],
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": current_stop['lat'] + random.uniform(-0.0005, 0.0005),
                "longitude": current_stop['lon'] + random.uniform(-0.0005, 0.0005)
            },
            "speed_kmh": random.randint(15, 50),
            "passengers": passengers,
            "crowdedness": crowdedness_level,
            "distance_to_stop_km": distance_to_stop_km
        }
    return status

def update_bus_operational_status(bus_id, is_running=None, status_message=None, crowdedness_level=None):
    """Admin/Driver API: Updates the persistent state of a bus."""
    if bus_id in BUS_OPERATIONAL_STATUS:
        state = BUS_OPERATIONAL_STATUS[bus_id]
        if is_running is not None: state["is_running"] = is_running
        if status_message is not None: state["status_message"] = status_message
        if crowdedness_level is not None: state["crowdedness_level"] = crowdedness_level
        # Re-assign a default route if it was previously 'N/A'
        if state.get("assigned_route_id") == "N/A" and is_running:
             state["assigned_route_id"] = f"Route-{random.choice([1, 2])}"
        return True
    return False

# Mock Analytics Data (Used by the Admin Panel)
ANALYTICS = {
    "total_trips": 100, "total_passengers": 5000, "avg_delay_minutes": 3.5,
    "busiest_route": "Route-1", "busiest_time": "5PM - 7PM",
}
