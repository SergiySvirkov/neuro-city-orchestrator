# src/data_ingestion/sumo_data_producer.py
import os
import sys
import time
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError

# --- Add SUMO tools to system path ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci
from sumo_scenario.generate_scenario import generate_scenario, CONFIG_FILE

# --- Configuration ---
KAFKA_BROKER_URL = 'kafka:29092' # Connect to the internal Kafka listener
KAFKA_TOPIC_NAME = 'smart_city_events'
SIMULATION_STEP_DELAY = 0.5 # Seconds to wait between simulation steps

# --- City coordinate mapping (for consistency with previous steps) ---
LATITUDE_CENTER = 50.4501
LONGITUDE_CENTER = 30.5234
# We'll map SUMO's (x,y) coordinates into this bounding box
X_MAX_SUMO = 1000 # Approximate max X from a 5x5 grid
Y_MAX_SUMO = 1000 # Approximate max Y

def create_kafka_producer():
    """Creates and returns a Kafka producer."""
    print("Connecting to Kafka...")
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Successfully connected to Kafka.")
            return producer
        except KafkaError:
            print("Failed to connect to Kafka. Retrying in 5 seconds...")
            time.sleep(5)

def format_vehicle_data(vehicle_id):
    """Fetches and formats data for a single vehicle from SUMO."""
    x, y = traci.vehicle.getPosition(vehicle_id)
    lon = LONGITUDE_CENTER + (x / X_MAX_SUMO - 0.5) * 0.1
    lat = LATITUDE_CENTER + (y / Y_MAX_SUMO - 0.5) * 0.1

    return {
        "event_type": "vehicle_traffic",
        "vehicle_id": vehicle_id,
        "timestamp": time.time(),
        "position": {"lat": lat, "lon": lon},
        "speed_kmh": round(traci.vehicle.getSpeed(vehicle_id) * 3.6, 2),
        "license_plate": f"SUMO-{vehicle_id}" # Simplified license plate
    }

def format_traffic_light_data(light_id):
    """Fetches and formats data for a single traffic light."""
    x, y = traci.trafficlight.getPosition(light_id)
    lon = LONGITUDE_CENTER + (x / X_MAX_SUMO - 0.5) * 0.1
    lat = LATITUDE_CENTER + (y / Y_MAX_SUMO - 0.5) * 0.1

    return {
        "event_type": "traffic_light_status",
        "light_id": light_id,
        "timestamp": time.time(),
        "position": {"lat": lat, "lon": lon},
        "state": traci.trafficlight.getRedYellowGreenState(light_id)
    }

def run_simulation():
    """Main simulation loop."""
    # 1. Ensure the SUMO scenario exists
    generate_scenario()

    # 2. Create Kafka Producer
    producer = create_kafka_producer()

    # 3. Start SUMO as a background process
    sumo_cmd = ["sumo", "-c", CONFIG_FILE]
    traci.start(sumo_cmd)
    print("SUMO simulation started.")

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            
            # --- Get and send vehicle data ---
            vehicle_ids = traci.vehicle.getIDList()
            for veh_id in vehicle_ids:
                vehicle_data = format_vehicle_data(veh_id)
                producer.send(KAFKA_TOPIC_NAME, key=veh_id.encode('utf-8'), value=vehicle_data)

            # --- Get and send traffic light data ---
            light_ids = traci.trafficlight.getIDList()
            for light_id in light_ids:
                light_data = format_traffic_light_data(light_id)
                producer.send(KAFKA_TOPIC_NAME, key=light_id.encode('utf-8'), value=light_data)

            producer.flush()
            print(f"Step: {traci.simulation.getTime()} | Vehicles: {len(vehicle_ids)} | Lights: {len(light_ids)}")
            time.sleep(SIMULATION_STEP_DELAY)

    except traci.TraCIException as e:
        print(f"Traci error: {e}")
    except KeyboardInterrupt:
        print("Simulation stopped by user.")
    finally:
        traci.close()
        producer.close()
        print("SUMO connection and Kafka producer closed.")

if __name__ == "__main__":
    run_simulation()
