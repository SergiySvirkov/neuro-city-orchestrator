# src/dashboard/dashboard_backend.py
import asyncio
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from kafka import KafkaConsumer

# --- FastAPI App Setup ---
app = FastAPI()
templates = Jinja2Templates(directory="src/dashboard/templates")

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- Kafka Consumer Task ---
def consume_kafka_messages():
    """
    Consumes messages from Kafka topics and broadcasts them to WebSocket clients.
    This function runs in a separate thread managed by asyncio.
    """
    consumer = KafkaConsumer(
        'smart_city_events', 
        'traffic_density_alerts',
        bootstrap_servers='kafka:29092', # Connect to internal Kafka
        group_id='dashboard-consumer-group',
        auto_offset_reset='latest'
    )
    print("Dashboard consumer connected to Kafka...")
    
    for message in consumer:
        try:
            data = json.loads(message.value.decode('utf-8'))
            
            # Add a specific event type for agent actions
            if message.topic == 'traffic_density_alerts':
                data['event_type'] = 'agent_action'
            
            # Broadcast the data to all connected clients
            asyncio.run(manager.broadcast(json.dumps(data)))
        except Exception as e:
            print(f"Error processing message: {e}")


@app.on_event("startup")
async def startup_event():
    """Run the Kafka consumer in a background task on app startup."""
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, consume_kafka_messages)

# --- API Endpoints ---
@app.get("/")
async def get_dashboard(request: Request):
    """Serves the main dashboard HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections from clients."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
