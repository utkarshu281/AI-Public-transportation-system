import os
import random
import numpy as np
import joblib
from flask import Flask, jsonify, request
from jinja2 import TemplateNotFound

# Local imports (Requires datasim.py and ai_models.py in the same folder)
import datasim
import ai_models


# --- AI Model Loading ---
try:
    # Loads the ETA model created by ai_models.py
    eta_model = joblib.load(ai_models.ETA_MODEL_FILE)
    print("AI ETA Model loaded successfully.")
except FileNotFoundError:
    print(f"ERROR: AI Models not found. Run 'python {ai_models.ETA_MODEL_FILE}' first.")
    eta_model = None


# --- Core Helper Functions ---

def mock_predict_eta(speed, distance):
    """Uses the loaded model or falls back to basic calculation."""
    return ai_models.predict_eta(eta_model, speed, distance)

def calculate_journey_time(speed, dist_to_start_km, start_name, end_name, route_id):
    """Mocks the complex A-to-B journey time calculation."""
    # 1. ETA to the START stop (boarding time)
    eta_to_start = mock_predict_eta(speed, dist_to_start_km)
    
    # 2. Travel time from START to END (A-to-B)
    stops_in_between = datasim.get_stops_in_order(route_id, start_name, end_name)
    # Mock travel time: 4-8 minutes per stop
    travel_time_ab = len(stops_in_between) * random.uniform(4, 8) 
    
    total_journey_time = eta_to_start + travel_time_ab
    
    return eta_to_start, total_journey_time


def create_app() -> Flask:
    # We explicitly do NOT use a template folder, serving index.html from root.
    app = Flask(__name__) 

    @app.route('/')
    def index():
        try:
            # Read and serve the index.html file directly from the root, bypassing Jinja2.
            with open('index.html', 'r') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        except FileNotFoundError:
            return "ERROR: index.html not found. Please ensure the file is in the root directory.", 500
        
        # --- Serve static files like app.js and style.css ---
    @app.route('/<path:filename>')
    def serve_static(filename):
        allowed = {'app.js', 'style.css'}
        if filename in allowed:
            from flask import send_from_directory
            return send_from_directory('.', filename)
        return "File not found", 404
    
    @app.route('/api/v1/plan', methods=['GET'])
    def get_route_plan():
        """Handles Start + Destination Input and Route Suggestions."""
        start = request.args.get('start')
        end = request.args.get('end')
        
        if not start or not end:
            return jsonify({'error': 'Start and end stop names are required'}), 400

        results = []
        all_routes = datasim.get_routes_metadata()
        
        try:
            live_data = datasim.generate_live_bus_status(num_buses=15)
        except Exception as e:
            print(f"Error generating live data: {e}")
            return jsonify({'error': 'Failed to generate live bus data.'}), 500
        
        for route_id, route_data in all_routes.items():
            stop_names = [s['name'] for s in route_data['stops']]
            
            # Ensure route has both stops before proceeding
            if start in stop_names and end in stop_names:
                
                for bus_id, bus_info in live_data.items():
                    if bus_info['route_id'] == route_id and bus_info['is_running']:
                        
                        speed = bus_info.get('speed_kmh', 20)
                        dist_to_start_km = random.uniform(0.5, 3.0) 
                        
                        eta_to_start, total_journey_time = calculate_journey_time(
                            speed, dist_to_start_km, start, end, route_id
                        )
                        
                        results.append({
                            'route_id': route_id,
                            'bus_id': bus_id,
                            'eta_to_start_min': f"{eta_to_start:.1f}",
                            'total_journey_min': f"{total_journey_time:.1f}",
                            'crowdedness': bus_info.get('crowdedness', 'N/A'),
                            'currentStop': bus_info.get('current_stop', start),
                            'endStop': end
                        })

        results.sort(key=lambda x: float(x['total_journey_min']))
        
        return jsonify({
            'start': start, 'end': end, 'suggestions': results
        }), 200

    @app.route('/api/v1/status', methods=['GET'])
    def get_status_v1():
        """Provides raw, real-time fleet status."""
        live_data = datasim.generate_live_bus_status(num_buses=15)
        
        status_list = []
        for bus_id, item in live_data.items():
            status_list.append({
                'bus_id': bus_id,
                'route_id': item['route_id'],
                'is_running': item['is_running'],
                'current_stop': item['current_stop'],
                'next_stop_name': item['next_stop_name'],
                'crowdedness': item['crowdedness'],
                'location': item['location'],
                'passengers': item['passengers'],
                'speed_kmh': item['speed_kmh'],
            })
        
        return jsonify(status_list), 200

    @app.route('/api/v1/analytics', methods=['GET'])
    def get_analytics():
        """Provides mock usage statistics."""
        return jsonify(datasim.ANALYTICS), 200
        
    @app.route('/api/admin/bus-update', methods=['POST'])
    def update_bus_status():
        """Admin/Driver API: Handles status updates (MOCK)."""
        payload = request.get_json(silent=True) or {}
        bus_id = payload.get('bus_id')
        
        success = datasim.update_bus_operational_status(
            bus_id=bus_id,
            is_running=payload.get('is_running'),
            status_message=payload.get('status_message'),
            crowdedness_level=payload.get('crowdedness_level')
        )
        
        if success:
            return jsonify({'status': 'ok', 'bus_id': bus_id}), 200
        else:
            return jsonify({'error': 'Bus not found in system'}), 404

    return app

# Flask discovers this as the default app when using `py run_app.py`
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
