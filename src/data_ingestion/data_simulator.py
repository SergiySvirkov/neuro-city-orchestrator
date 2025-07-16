# src/data_ingestion/data_simulator.py

import time
import random
import json
import uuid
import numpy as np
from faker import Faker

# --- Configuration ---
# City center coordinates (e.g., Kyiv)
LATITUDE_CENTER = 50.4501
LONGITUDE_CENTER = 30.5234
COORDINATE_DEVIATION = 0.05  # The radius of our simulated city area

# Number of simulated devices
NUM_VEHICLES = 100
NUM_TRAFFIC_LIGHTS = 20
NUM_AIR_QUALITY_SENSORS = 10

# Simulation parameters
SIMULATION_INTERVAL_SECONDS = 1  # How often to generate new data
VEHICLE_SPEED_KMH_MIN = 5
VEHICLE_SPEED_KMH_MAX = 60
CO2_PPM_MIN = 400
CO2_PPM_MAX = 1000
PM25_UG_M3_MIN = 5
PM25_UG_M3_MAX = 50

# Initialize Faker for generating unique IDs
fake = Faker()

def generate_initial_state(num_vehicles, num_traffic_lights, num_air_sensors):
    """Generates the initial state for all simulated devices."""
    state = {
        "vehicles": [
            {
                "vehicle_id": str(uuid.uuid4()),
                "license_plate": fake.license_plate(),
                "position": {
                    "lat": LATITUDE_CENTER + random.uniform(-COORDINATE_DEVIATION, COORDINATE_DEVIATION),
                    "lon": LONGITUDE_CENTER + random.uniform(-COORDINATE_DEVIATION, COORDINATE_DEVIATION),
                },
            } for _ in range(num_vehicles)
        ],
        "traffic_lights": [
            {
                "light_id": f"TL-{i+1}",
                "position": {
                    "lat": LATITUDE_CENTER + random.uniform(-COORDINATE_DEVIATION, COORDINATE_DEVIATION),
                    "lon": LONGITUDE_CENTER + random.uniform(-COORDINATE_DEVIATION, COORDINATE_DEVIATION),
                },
                "state": random.choice(["RED", "GREEN"]),
                "last_changed": time.time()
            } for i in range(num_traffic_lights)
        ],
        "air_sensors": [
            {
                "sensor_id": f"AQS-{i+1}",
                "position": {
                    "lat": LATITUDE_CENTER + random.uniform(-COORDINATE_DEVIATION, COORDINATE_DEVIATION),
                    "lon": LONGITUDE_CENTER + random.uniform(-COORDINATE_DEVIATION, COORDINATE_DEVIATION),
                },
            } for i in range(num_air_sensors)
        ],
    }
    return state

def update_vehicle_data(vehicle):
    """Updates a vehicle's position and generates a data event."""
    # Simulate movement by adding a small random vector to the position
    movement_lat = random.uniform(-0.0005, 0.0005)
    movement_lon = random.uniform(-0.0005, 0.0005)
    vehicle["position"]["lat"] += movement_lat
    vehicle["position"]["lon"] += movement_lon
    
    # Clamp coordinates to stay within the city bounds
    vehicle["position"]["lat"] = max(min(vehicle["position"]["lat"], LATITUDE_CENTER + COORDINATE_DEVIATION), LATITUDE_CENTER - COORDINATE_DEVIATION)
    vehicle["position"]["lon"] = max(min(vehicle["position"]["lon"], LONGITUDE_CENTER + COORDINATE_DEVIATION), LONGITUDE_CENTER - COORDINATE_DEVIATION)

    return {
        "event_type": "vehicle_traffic",
        "vehicle_id": vehicle["vehicle_id"],
        "license_plate": vehicle["license_plate"],
        "timestamp": time.time(),
        "position": vehicle["position"],
        "speed_kmh": random.randint(VEHICLE_SPEED_KMH_MIN, VEHICLE_SPEED_KMH_MAX),
    }

def update_traffic_light_data(traffic_light):
    """Updates a traffic light's state and generates a data event."""
    # Change state every 30-60 seconds
    if time.time() - traffic_light["last_changed"] > random.randint(30, 60):
        traffic_light["state"] = "GREEN" if traffic_light["state"] == "RED" else "RED"
        traffic_light["last_changed"] = time.time()

    return {
        "event_type": "traffic_light_status",
        "light_id": traffic_light["light_id"],
        "timestamp": time.time(),
        "position": traffic_light["position"],
        "state": traffic_light["state"],
    }

def generate_air_quality_data(sensor):
    """Generates an air quality data event."""
    return {
        "event_type": "air_quality",
        "sensor_id": sensor["sensor_id"],
        "timestamp": time.time(),
        "position": sensor["position"],
        "co2_ppm": np.random.normal(loc=(CO2_PPM_MAX + CO2_PPM_MIN) / 2, scale=50),
        "pm2_5_ug_m3": np.random.normal(loc=(PM25_UG_M3_MAX + PM25_UG_M3_MIN) / 2, scale=5),
    }

def run_simulation():
    """Main simulation loop."""
    print("Starting data simulation... Press Ctrl+C to stop.")
    
    # Initialize the state of all devices
    current_state = generate_initial_state(NUM_VEHICLES, NUM_TRAFFIC_LIGHTS, NUM_AIR_QUALITY_SENSORS)

    while True:
        try:
            # Generate and print data for a random selection of devices each second
            # This simulates asynchronous real-world events
            
            # 1. Update a random vehicle
            vehicle_to_update = random.choice(current_state["vehicles"])
            vehicle_event = update_vehicle_data(vehicle_to_update)
            print(json.dumps(vehicle_event))

            # 2. Update a random traffic light (less frequently)
            if random.random() < 0.2: # ~20% chance each second
                light_to_update = random.choice(current_state["traffic_lights"])
                light_event = update_traffic_light_data(light_to_update)
                print(json.dumps(light_event))

            # 3. Get a reading from a random air quality sensor (less frequently)
            if random.random() < 0.1: # ~10% chance each second
                sensor_to_read = random.choice(current_state["air_sensors"])
                air_quality_event = generate_air_quality_data(sensor_to_read)
                print(json.dumps(air_quality_event))

            time.sleep(SIMULATION_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # To make this directory a package, create an empty __init__.py file
    # in src/data_ingestion/
    run_simulation()
