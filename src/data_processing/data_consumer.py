# src/data_processing/data_consumer.py

import json
import os
import pandas as pd
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# --- Configuration ---
KAFKA_BROKER_URL = 'localhost:9092'
KAFKA_TOPIC_NAME = 'smart_city_events'
KAFKA_GROUP_ID = 'smart-city-storage-group' # Consumer group ID

# Directory to store the output CSV files
OUTPUT_DIR = 'data/raw' 

def create_kafka_consumer(topic, group_id):
    """Creates and returns a Kafka consumer."""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BROKER_URL,
            group_id=group_id,
            auto_offset_reset='earliest',  # Start reading from the beginning of the topic
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            # Add some retry logic for robustness
            reconnect_backoff_ms=5000,
            reconnect_backoff_max_ms=100000
        )
        print("Successfully connected to Kafka and subscribed to topic.")
        return consumer
    except KafkaError as e:
        print(f"Error connecting to Kafka: {e}")
        return None

def store_data_as_csv(data):
    """
    Identifies the event type and appends the data to the corresponding CSV file.
    Creates the file and writes the header if it doesn't exist.
    """
    event_type = data.get('event_type')
    if not event_type:
        print(f"Warning: Received message without event_type: {data}")
        return

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Define file paths for different event types
    file_path = os.path.join(OUTPUT_DIR, f"{event_type}.csv")

    # Convert the single data record to a pandas DataFrame
    df = pd.DataFrame([data])

    # Check if file exists to decide whether to write the header
    write_header = not os.path.exists(file_path)

    # Append data to the CSV file
    try:
        df.to_csv(file_path, mode='a', header=write_header, index=False)
        # print(f"Stored {event_type} event to {file_path}")
    except Exception as e:
        print(f"Error writing to CSV file {file_path}: {e}")


def consume_and_store():
    """
    Main loop to consume messages from Kafka and store them.
    """
    consumer = create_kafka_consumer(KAFKA_TOPIC_NAME, KAFKA_GROUP_ID)
    if not consumer:
        print("Exiting: Could not create Kafka consumer.")
        return

    print(f"Listening for messages on topic '{KAFKA_TOPIC_NAME}'... Press Ctrl+C to stop.")

    for message in consumer:
        try:
            # message.value is already deserialized by the consumer
            data = message.value
            print(f"Received message: {data}")
            
            # --- Storage Logic ---
            # Option 1: Store as CSV (Implemented)
            store_data_as_csv(data)

            # Option 2: Store in PostgreSQL/TimescaleDB (Future Step)
            # Here you would call a function like:
            # store_in_timescaledb(data)
            # This function would require a connection (e.g., using psycopg2)
            # and would execute an INSERT statement into the appropriate table
            # based on the event_type.

        except json.JSONDecodeError:
            print(f"Warning: Could not decode message: {message.value}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    consume_and_store()
