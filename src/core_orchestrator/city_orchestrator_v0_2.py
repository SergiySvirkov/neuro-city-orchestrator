# src/core_orchestrator/city_orchestrator_v0_2.py

import json
import os
import sys
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# --- Add project root to Python path ---
# This allows us to import modules from the 'src' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.agents.incident_reporter_crew import create_and_run_crew

# --- Configuration ---
KAFKA_BROKER_URL = 'localhost:9092'
INPUT_TOPIC = 'traffic_density_alerts'
CONSUMER_GROUP_ID = 'city-orchestrator-group-v2'
TRAFFIC_THRESHOLD = 30

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def create_kafka_consumer(topic, group_id):
    # (This function is identical to the previous version)
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BROKER_URL,
            group_id=group_id,
            auto_offset_reset='latest',
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        print(f"{BColors.OKGREEN}Successfully connected to Kafka.{BColors.ENDC}")
        print(f"Listening for alerts on topic '{BColors.OKCYAN}{topic}{BColors.ENDC}'...")
        return consumer
    except KafkaError as e:
        print(f"{BColors.FAIL}Error connecting to Kafka: {e}{BColors.ENDC}")
        return None

def run_orchestrator():
    consumer = create_kafka_consumer(INPUT_TOPIC, CONSUMER_GROUP_ID)
    if not consumer:
        return
        
    print("-" * 50)
    print(f"{BColors.BOLD}City Orchestrator v0.2 (AI Agent Enabled) is running.{BColors.ENDC}")
    print(f"Threshold set to > {BColors.WARNING}{TRAFFIC_THRESHOLD}{BColors.ENDC} vehicles/minute.")
    print("-" * 50)

    for message in consumer:
        try:
            alert_data = message.value
            district = alert_data.get('district')
            vehicle_count = alert_data.get('vehicle_count')

            if not district or vehicle_count is None:
                continue
            
            print(f"Received data: District '{district}' has {vehicle_count} vehicles.")

            if vehicle_count > TRAFFIC_THRESHOLD:
                # --- Integration with CrewAI ---
                # Instead of just printing, we now trigger the AI agent crew
                ai_generated_report = create_and_run_crew(district, vehicle_count)
                
                print("\n" + "="*20 + " AI AGENT REPORT " + "="*20)
                print(f"{BColors.HEADER}{ai_generated_report}{BColors.ENDC}")
                print("="*58 + "\n")

        except Exception as e:
            print(f"{BColors.FAIL}An unexpected error occurred: {e}{BColors.ENDC}")

if __name__ == "__main__":
    try:
        run_orchestrator()
    except KeyboardInterrupt:
        print(f"\n{BColors.BOLD}Orchestrator stopped by user.{BColors.ENDC}")
