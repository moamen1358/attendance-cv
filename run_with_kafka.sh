#!/bin/bash

# Start Kafka and Zookeeper containers
echo "Starting Kafka and Zookeeper containers..."
docker run -d --name zookeeper -p 2181:2181 -e ALLOW_ANONYMOUS_LOGIN=yes bitnami/zookeeper:latest
docker run -d --name kafka -p 9092:9092 -e KAFKA_CFG_ZOOKEEPER_CONNECT=host.docker.internal:2181 -e ALLOW_PLAINTEXT_LISTENER=yes -e KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 bitnami/kafka:latest

# Wait for Kafka to be fully available
echo "Waiting for Kafka to be ready..."
sleep 15

# Create the Kafka topic (if it doesn't exist)
echo "Creating Kafka topic 'attendance_events'..."
docker exec -it kafka kafka-topics.sh --create --if-not-exists --topic attendance_events --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Run the Streamlit app directly
echo "Starting the app with Kafka support..."
cd "$(dirname "$0")"
python -m streamlit run src/login.py --server.port=8501

# To stop Kafka when done, run:
# docker stop kafka zookeeper && docker rm kafka zookeeper