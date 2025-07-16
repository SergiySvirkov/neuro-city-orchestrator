# src/data_processing/realtime_aggregator.py

import json
from pyflink.common import WatermarkStrategy, Time
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaSink, KafkaRecordSerializationSchema
from pyflink.datastream.formats.json import JsonRowDeserializationSchema, JsonRowSerializationSchema
from pyflink.datastream.window import TumblingProcessingTimeWindows

# --- Configuration ---
KAFKA_BROKER_URL = 'kafka:9092' # Use the internal Docker network name
INPUT_TOPIC = 'smart_city_events'
OUTPUT_TOPIC = 'traffic_density_alerts'
FLINK_JOB_NAME = 'Real-time Traffic Aggregator'

# City center coordinates (from simulator)
LATITUDE_CENTER = 50.4501
LONGITUDE_CENTER = 30.5234

def get_district(lat, lon):
    """Assigns a geo-coordinate to a predefined city district."""
    if lat >= LATITUDE_CENTER and lon < LONGITUDE_CENTER:
        return "District A (North-West)"
    elif lat >= LATITUDE_CENTER and lon >= LONGITUDE_CENTER:
        return "District B (North-East)"
    elif lat < LATITUDE_CENTER and lon < LONGITUDE_CENTER:
        return "District C (South-West)"
    else:
        return "District D (South-East)"

def run_flink_job():
    """
    Defines and executes the Flink streaming job.
    """
    # 1. Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    # Required for Kafka connectors
    env.add_jars("file:///opt/flink/lib/flink-sql-connector-kafka-1.15.2.jar")

    # 2. Define the Kafka Source (Input)
    # Define the schema of the incoming JSON data
    source_type_info = Types.ROW_NAMED(
        ['event_type', 'vehicle_id', 'timestamp', 'position', 'speed_kmh', 'license_plate'],
        [Types.STRING(), Types.STRING(), Types.DOUBLE(), Types.MAP(Types.STRING(), Types.DOUBLE()), Types.INT(), Types.STRING()]
    )
    
    source = KafkaSource.builder() \
        .set_bootstrap_servers(KAFKA_BROKER_URL) \
        .set_topics(INPUT_TOPIC) \
        .set_group_id("flink-traffic-aggregator-group") \
        .set_starting_offsets("earliest") \
        .set_value_only_deserializer(JsonRowDeserializationSchema.builder().type_info(source_type_info).build()) \
        .build()

    # 3. Define the data processing pipeline
    data_stream = env.from_source(source, WatermarkStrategy.no_watermarks(), "Kafka Source")

    # a. Filter for vehicle traffic events only
    vehicle_stream = data_stream.filter(lambda row: row['event_type'] == 'vehicle_traffic')

    # b. Map to a (district, 1) tuple for counting
    district_stream = vehicle_stream.map(
        lambda row: (get_district(row['position']['lat'], row['position']['lon']), 1),
        output_type=Types.TUPLE([Types.STRING(), Types.INT()])
    )

    # c. Key by district and apply a tumbling window of 1 minute
    # Then sum the counts in each window
    aggregated_stream = district_stream \
        .key_by(lambda x: x[0]) \
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1))) \
        .reduce(lambda v1, v2: (v1[0], v1[1] + v2[1]))

    # d. Format the output for the sink
    # We convert the tuple (district, count) to a JSON row
    output_type_info = Types.ROW_NAMED(['district', 'vehicle_count', 'timestamp'], [Types.STRING(), Types.INT(), Types.STRING()])
    
    def format_output(agg_tuple):
        district, count = agg_tuple
        # Using processing time as the event timestamp for this simple aggregation
        return {'district': district, 'vehicle_count': count, 'timestamp': str(time.time())}

    json_output_stream = aggregated_stream.map(
        lambda row: json.dumps(format_output(row)),
        output_type=Types.STRING()
    )


    # 4. Define the Kafka Sink (Output)
    sink = KafkaSink.builder() \
        .set_bootstrap_servers(KAFKA_BROKER_URL) \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
                .set_topic(OUTPUT_TOPIC)
                .set_value_serialization_schema(lambda x: x.encode('utf-8'))
                .build()
        ) \
        .build()

    # 5. Attach the sink to the stream
    json_output_stream.sink_to(sink)

    # 6. Execute the job
    print(f"Submitting Flink job: '{FLINK_JOB_NAME}'")
    env.execute(FLINK_JOB_NAME)


if __name__ == "__main__":
    run_flink_job()
