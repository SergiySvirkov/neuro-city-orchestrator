# kafka_topic_viewer.py
# A simple utility to consume and print messages from a specific Kafka topic.
# Usage: python kafka_topic_viewer.py <topic_name>

import sys
from kafka import KafkaConsumer

def view_topic(broker_url, topic_name):
    """Connects to Kafka and prints messages from the specified topic."""
    try:
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=broker_url,
            auto_offset_reset='earliest', # Start from the beginning
            consumer_timeout_ms=30000 # Stop if no messages for 30s
        )
        print(f"Listening to topic '{topic_name}'... (Will stop after 30s of inactivity)")
        
        message_count = 0
        for message in consumer:
            print(f"Offset: {message.offset}, Key: {message.key}, Value: {message.value.decode('utf-8')}")
            message_count += 1
            
        if message_count == 0:
            print("No messages found in the topic.")
        else:
            print(f"\nFinished reading. Total messages: {message_count}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kafka_topic_viewer.py <topic_name>")
        sys.exit(1)
        
    KAFKA_BROKER = 'localhost:9092'
    topic = sys.argv[1]
    view_topic(KAFKA_BROKER, topic)
