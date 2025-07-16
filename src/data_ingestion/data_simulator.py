# src/data_ingestion/data_simulator.py

import time
import random
import json
import uuid
import numpy as np
from faker import Faker
from kafka import KafkaProducer
from kafka.errors import KafkaError

# --- Kafka Configuration ---
KAFKA_BROKER_URL = 'localhost:9092'
KAFKA_TOPIC_NAME = 'smart_city_events'

# --- Simulation Configuration ---
LATITUDE_CENTER = 50.4501
LONGITUDE_CENTER = 30.5234
COORDINATE_DEVIATION = 0.05

NUM_VEHICLES = 100
NUM_TRAFFIC_LIGHTS = 20
NUM_AIR_QUALITY_SENSORS = 10

SIMULATION_INTERVAL_SECONDS = 1
VEHICLE_SPEED_KMH_MIN = 5
VEHICLE_SPEED_KMH_MAX = 60
CO2_PPM_MIN = 400
CO2_PPM_MAX = 1000
PM25_UG_M3_MIN = 5
PM25_UG_M3_MAX = 50

fake = Faker()

def create_kafka_producer():
    """Creates and returns a Kafka producer."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            # Add some retry logic for robustness
            retries=5,
            request_timeout_ms=30000
        )
        print("Successfully connected to Kafka.")
        return producer
    except KafkaError as e:
        print(f"Error connecting to Kafka: {e}")
        return None

def generate_initial_state(num_vehicles, num_traffic_lights, num_air_sensors):
    """Generates the initial state for all simulated devices."""
    # (This function remains unchanged from the previous version)
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

# --- Data generation functions (update_vehicle_data, etc.) remain unchanged ---
# ... (The functions update_vehicle_data, update_traffic_light_data, 
# ... and generate_air_quality_data are identical to the previous step)
def update_vehicle_data(vehicle):
    movement_lat = random.uniform(-0.0005, 0.0005)
    movement_lon = random.uniform(-0.0005, 0.0005)
    vehicle["position"]["lat"] += movement_lat
    vehicle["position"]["lon"] += movement_lon
    vehicle["position"]["lat"] = max(min(vehicle["position"]["lat"], LATITUDE_CENTER + COORDINATE_DEVIATION), LATITUDE_CENTER - COORDINATE_DEVIATION)
    vehicle["position"]["lon"] = max(min(vehicle["position"]["lon"], LONGITUDE_CENTER + COORDINATE_DEVIATION), LONGITUDE_CENTER - COORDINATE_DEVIATION)
    return { "event_type": "vehicle_traffic", "vehicle_id": vehicle["vehicle_id"], "license_plate": vehicle["license_plate"], "timestamp": time.time(), "position": vehicle["position"], "speed_kmh": random.randint(VEHICLE_SPEED_KMH_MIN, VEHICLE_SPEED_KMH_MAX) }
def update_traffic_light_data(traffic_light):
    if time.time() - traffic_light["last_changed"] > random.randint(30, 60):
        traffic_light["state"] = "GREEN" if traffic_light["state"] == "RED" else "RED"
        traffic_light["last_changed"] = time.time()
    return { "event_type": "traffic_light_status", "light_id": traffic_light["light_id"], "timestamp": time.time(), "position": traffic_light["position"], "state": traffic_light["state"] }
def generate_air_quality_data(sensor):
    return { "event_type": "air_quality", "sensor_id": sensor["sensor_id"], "timestamp": time.time(), "position": sensor["position"], "co2_ppm": np.random.normal(loc=(CO2_PPM_MAX + CO2_PPM_MIN) / 2, scale=50), "pm2_5_ug_m3": np.random.normal(loc=(PM25_UG_M3_MAX + PM25_UG_M3_MIN) / 2, scale=5) }
# --- End of unchanged functions ---

def run_simulation():
    """Main simulation loop that sends data to Kafka."""
    producer = create_kafka_producer()
    if not producer:
        print("Exiting: Could not create Kafka producer.")
        return

    print(f"Starting data simulation... Sending events to Kafka topic: '{KAFKA_TOPIC_NAME}'. Press Ctrl+C to stop.")
    
    current_state = generate_initial_state(NUM_VEHICLES, NUM_TRAFFIC_LIGHTS, NUM_AIR_QUALITY_SENSORS)

    while True:
        try:
            # Generate event data
            vehicle_to_update = random.choice(current_state["vehicles"])
            vehicle_event = update_vehicle_data(vehicle_to_update)
            
            # Send to Kafka
            producer.send(KAFKA_TOPIC_NAME, key=vehicle_event['vehicle_id'].encode('utf-8'), value=vehicle_event)
            print(f"Sent event for vehicle: {vehicle_event['vehicle_id']}")

            if random.random() < 0.2:
                light_to_update = random.choice(current_state["traffic_lights"])
                light_event = update_traffic_light_data(light_to_update)
                producer.send(KAFKA_TOPIC_NAME, key=light_event['light_id'].encode('utf-8'), value=light_event)
                print(f"Sent event for traffic light: {light_event['light_id']}")

            if random.random() < 0.1:
                sensor_to_read = random.choice(current_state["air_sensors"])
                air_quality_event = generate_air_quality_data(sensor_to_read)
                producer.send(KAFKA_TOPIC_NAME, key=air_quality_event['sensor_id'].encode('utf-8'), value=air_quality_event)
                print(f"Sent event for air sensor: {air_quality_event['sensor_id']}")

            # Flush messages occasionally to ensure they are sent
            if random.random() < 0.05:
                producer.flush()

            time.sleep(SIMULATION_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nSimulation stopped by user. Flushing final messages...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)
    
    # Ensure all buffered messages are sent before exiting
    producer.flush()
    producer.close()
    print("Kafka producer closed.")

if __name__ == "__main__":
    run_simulation()
