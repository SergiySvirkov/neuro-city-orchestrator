Neuro-Orchestrator for Smart City & Autonomous Transport

Current Status: MVP 2 - Closed-Loop Control System Complete

This repository contains the source code for the "Neuro-Orchestrator" project, a B2B platform designed to serve as the centralized "brain" for a future smart city. The project currently exists as a fully functional, end-to-end prototype that simulates urban traffic, analyzes it in real-time, uses an AI agent crew to make decisions, and acts upon those decisions to mitigate congestion within the simulation.
Project Architecture (MVP 2)

The current system operates on a sophisticated, real-time data pipeline:

    Data Generation: The sumo_runner service runs a microscopic traffic simulation (SUMO), generating realistic data for vehicle positions and traffic light states.

    Data Streaming: This raw data is continuously streamed into an smart_city_events topic in Apache Kafka.

    Real-Time Analytics: An Apache Flink job consumes the raw data, aggregates it into 1-minute windows, and calculates traffic density for predefined city districts. High-density alerts are published to a new Kafka topic, traffic_density_alerts.

    AI-Powered Decision Making: The city_orchestrator service listens for these alerts. Upon detecting an incident, it triggers a CrewAI team of AI agents.

    Closed-Loop Control: The AI crew analyzes the incident, formulates a mitigation plan, and uses a custom tool (via SUMO's Traci API) to directly modify the simulation, for example, by extending a traffic light's green phase.

    Live Visualization: A dashboard service (FastAPI + WebSockets) consumes data from both Kafka topics and pushes it to a web interface, providing a live map-based view of traffic and AI actions.

How to Run the Prototype

To run the complete simulation and dashboard on your local machine:

Prerequisites:

    Docker and Docker Compose

    Python 3.9+

    An API key from Google AI Studio for the Gemini model

Steps:

    Clone the repository:

    git clone <your-repository-url>
    cd neuro-city-orchestrator

    Set up environment variables:

        Copy the .env.example file to a new file named .env.

        Open .env and add your GEMINI_API_KEY.

    Install Python dependencies:

    pip install -r requirements.txt

    Build and start all services:

        This command will build the custom Docker images and start all services (SUMO, Kafka, Flink, Dashboard) in the background.

    docker-compose build
    docker-compose up -d

    Start the processing and logic scripts:

        Open two separate terminal windows.

        In the first terminal, start the Flink analytics job:

        python src/data_processing/realtime_aggregator.py

        In the second terminal, start the City Orchestrator:

        python src/core_orchestrator/city_orchestrator_v0_3.py

    View the dashboard:

        Open your web browser and navigate to http://localhost:8000. You will see the live simulation map.

Future Roadmap

This functional prototype serves as the foundation for several advanced development phases:
Phase 4: Advanced Agent Functionality

    Proactive Route Planning: Develop agents that can proactively reroute vehicles around predicted congestion zones before they form.

    Energy Management: Integrate agents to manage a network of simulated EV charging stations, optimizing charging schedules based on vehicle demand and grid load.

    Advanced LLM Integration: Upgrade the core "City Orchestrator" to use a more powerful LLM (e.g., Mistral) for complex, multi-variable strategic planning beyond simple incident response.

Phase 5: Immersive Interface Integration (Proof of Concept)

    VR/AR Simulation: Develop a client using a game engine (Unity/Unreal) that connects to the simulation data, allowing an operator to "fly through" the virtual city and visualize data overlays in an immersive 3D environment.

    BCI for Enhanced Operations: Create a proof-of-concept application using a consumer-grade BCI headset (e.g., Muse). The app will monitor an operator's cognitive state (e.g., focus) and automatically highlight critical incidents on the dashboard when high focus is detected, demonstrating a basic "NeuroFlow" interaction.

Phase 6: Pilot Deployment

    Hardware Integration: Partner with a technology park, university campus, or logistics hub to deploy a small number of real IoT sensors (traffic cameras, environmental sensors).

    Real-World Data Fusion: Adapt the data ingestion pipeline to process and fuse data from both the real-world sensors and the ongoing simulation, allowing for robust testing and validation in a controlled, real-world environment.
