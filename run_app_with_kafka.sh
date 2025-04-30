#!/bin/bash

# Check if Kafka topic 'attendance_events' exists, create if not
echo "Checking Kafka topic 'attendance_events'..."
docker exec my_grad_streamlit-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list | grep attendance_events > /dev/null
if [ $? -ne 0 ]; then
    echo "Creating Kafka topic 'attendance_events'..."
    docker exec my_grad_streamlit-kafka-1 kafka-topics --create --topic attendance_events --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
else
    echo "Kafka topic 'attendance_events' already exists."
fi

# Run Streamlit app directly
echo "Starting the app with Kafka support..."
cd "$(dirname "$0")"
python -m streamlit run src/login.py --server.port=8501

# Note: To stop Kafka and Zookeeper containers, run:
# docker stop my_grad_streamlit-kafka-1 my_grad_streamlit-zookeeper-1