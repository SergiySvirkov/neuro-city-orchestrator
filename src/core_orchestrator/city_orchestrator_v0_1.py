# src/core_orchestrator/city_orchestrator_v0_1.py

import json
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# --- Configuration ---
KAFKA_BROKER_URL = 'localhost:9092'
INPUT_TOPIC = 'traffic_density_alerts'  # The topic with aggregated data from Flink
CONSUMER_GROUP_ID = 'city-orchestrator-group'

# The core logic of our v0.1 orchestrator: a simple rule-based threshold.
TRAFFIC_THRESHOLD = 30 # Trigger an alert if vehicle count in a district exceeds this per minute.

# ANSI color codes for standout console output
class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def create_kafka_consumer(topic, group_id):
    """Creates and returns a Kafka consumer for the alerts topic."""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BROKER_URL,
            group_id=group_id,
            auto_offset_reset='latest',  # We only care about the most recent alerts
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        print(f"{BColors.OKGREEN}Successfully connected to Kafka.{BColors.ENDC}")
        print(f"Listening for traffic density alerts on topic '{BColors.OKCYAN}{topic}{BColors.ENDC}'...")
        return consumer
    except KafkaError as e:
        print(f"{BColors.FAIL}Error connecting to Kafka: {e}{BColors.ENDC}")
        return None

def run_orchestrator():
    """
    Main loop to consume aggregated data and apply rules.
    """
    consumer = create_kafka_consumer(INPUT_TOPIC, CONSUMER_GROUP_ID)
    if not consumer:
        print("Exiting: Could not create Kafka consumer.")
        return
        
    print("-" * 50)
    print(f"{BColors.BOLD}City Orchestrator v0.1 is running.{BColors.ENDC}")
    print(f"Alerting threshold set to > {BColors.WARNING}{TRAFFIC_THRESHOLD}{BColors.ENDC} vehicles/minute per district.")
    print("-" * 50)

    for message in consumer:
        try:
            alert_data = message.value
            district = alert_data.get('district')
            vehicle_count = alert_data.get('vehicle_count')

            if not district or vehicle_count is None:
                print(f"{BColors.WARNING}Warning: Received malformed message: {alert_data}{BColors.ENDC}")
                continue
            
            print(f"Received data: District '{district}' has {vehicle_count} vehicles.")

            # --- Core Rule Engine ---
            if vehicle_count > TRAFFIC_THRESHOLD:
                trigger_alert(district, vehicle_count)

        except json.JSONDecodeError:
            print(f"{BColors.WARNING}Warning: Could not decode message: {message.value}{BColors.ENDC}")
        except Exception as e:
            print(f"{BColors.FAIL}An unexpected error occurred: {e}{BColors.ENDC}")

def trigger_alert(district, vehicle_count):
    """
    This function simulates taking action based on a triggered rule.
    In a real system, this could:
    - Send an API call to a traffic management system.
    - Create a task for an AI agent (next step).
    - Log the event to a monitoring dashboard.
    - Send a notification to human operators.
    """
    print("\n" + "="*20 + " ALERT " + "="*20)
    print(f"{BColors.FAIL}{BColors.BOLD}High Traffic Density Detected!{BColors.ENDC}")
    print(f"  -> District: {BColors.OKCYAN}{district}{BColors.ENDC}")
    print(f"  -> Vehicle Count: {BColors.WARNING}{vehicle_count}{BColors.ENDC} (Threshold: {TRAFFIC_THRESHOLD})")
    print(f"  -> Action: {BColors.HEADER}Initiating traffic mitigation protocol for this district...{BColors.ENDC}")
    print("="*47 + "\n")


if __name__ == "__main__":
    # Create the directory structure if it doesn't exist
    import os
    os.makedirs('src/core_orchestrator', exist_ok=True)
    with open('src/core_orchestrator/__init__.py', 'a'):
        pass
        
    try:
        run_orchestrator()
    except KeyboardInterrupt:
        print(f"\n{BColors.BOLD}Orchestrator stopped by user.{BColors.ENDC}")

