# src/core_orchestrator/city_orchestrator_v0_3.py

import json
import os
import sys
from kafka import KafkaConsumer
from kafka.errors import KafkaError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# Import the NEW crew version
from src.agents.incident_reporter_crew_v2 import create_and_run_crew_v2

# --- Configuration & Setup (mostly unchanged) ---
KAFKA_BROKER_URL = 'localhost:9092'
INPUT_TOPIC = 'traffic_density_alerts'
CONSUMER_GROUP_ID = 'city-orchestrator-group-v3'
TRAFFIC_THRESHOLD = 20 # Lowered threshold for easier testing

class BColors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def create_kafka_consumer(topic, group_id):
    # (Identical to previous versions)
    try:
        consumer = KafkaConsumer(topic, bootstrap_servers=KAFKA_BROKER_URL, group_id=group_id, auto_offset_reset='latest', value_deserializer=lambda v: json.loads(v.decode('utf-8')))
        print(f"{BColors.OKGREEN}Successfully connected to Kafka.{BColors.ENDC}")
        return consumer
    except KafkaError as e:
        print(f"{BColors.FAIL}Error connecting to Kafka: {e}{BColors.ENDC}")
        return None

def run_orchestrator():
    consumer = create_kafka_consumer(INPUT_TOPIC, CONSUMER_GROUP_ID)
    if not consumer: return

    print("-" * 50)
    print(f"{BColors.BOLD}City Orchestrator v0.3 (Closed Loop Control) is running.{BColors.ENDC}")
    print(f"Threshold set to > {BColors.WARNING}{TRAFFIC_THRESHOLD}{BColors.ENDC} vehicles/minute.")
    print("-" * 50)

    for message in consumer:
        try:
            alert_data = message.value
            district = alert_data.get('district')
            vehicle_count = alert_data.get('vehicle_count')

            if not district or vehicle_count is None: continue
            
            print(f"Received data: District '{district}' has {vehicle_count} vehicles.")

            if vehicle_count > TRAFFIC_THRESHOLD:
                # --- Trigger the enhanced CrewAI crew ---
                final_result = create_and_run_crew_v2(district, vehicle_count)
                
                print("\n" + "="*20 + " FINAL SYSTEM RESPONSE " + "="*20)
                print(f"{BColors.OKGREEN}{final_result}{BColors.ENDC}")
                print("="*61 + "\n")

        except Exception as e:
            print(f"{BColors.FAIL}An unexpected error occurred: {e}{BColors.ENDC}")

if __name__ == "__main__":
    try:
        run_orchestrator()
    except KeyboardInterrupt:
        print(f"\n{BColors.BOLD}Orchestrator stopped by user.{BColors.ENDC}")
