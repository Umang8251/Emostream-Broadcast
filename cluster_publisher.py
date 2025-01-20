#!/usr/bin/env python3 
from kafka import KafkaConsumer
import json
import websockets
import asyncio
import sys

# WebSocket connection for broadcasting data
async def broadcast_to_websocket_server(websocket, emoji_data):
    """Send emoji data to the WebSocket server over a persistent connection."""
    try:
        await websocket.send(json.dumps(emoji_data))
        print(f"Sent to WebSocket server: {emoji_data}")
    except Exception as e:
        print(f"Error broadcasting to WebSocket server: {e}")
        raise

async def connect_with_retries(uri, max_retries=5, backoff_factor=2):
    """Attempt to connect to the WebSocket server with retries."""
    retries = 0
    while retries < max_retries:
        try:
            print(f"Connecting to WebSocket server at {uri} (attempt {retries + 1})...")
            websocket = await websockets.connect(uri)
            print("Connected successfully!")
            return websocket
        except Exception as e:
            print(f"Connection failed: {e}. Retrying in {backoff_factor ** retries} seconds...")
            await asyncio.sleep(backoff_factor ** retries)
            retries += 1
    raise ConnectionError(f"Failed to connect to {uri} after {max_retries} retries")

async def persistent_websocket_connection(uri, consumer):
    """Maintain a persistent WebSocket connection and broadcast messages."""
    websocket = None
    while True:
        try:
            # Reconnect if websocket is None or closed
            if websocket is None or websocket.closed:
                websocket = await connect_with_retries(uri)
            for message in consumer:
                print(f"Cluster received: {message.value}")
                await broadcast_to_websocket_server(websocket, message.value)
        except websockets.ConnectionClosedError:
            print("WebSocket connection closed, reconnecting...")
            websocket = None
        except Exception as e:
            print(f"Error maintaining WebSocket connection: {e}")
            await asyncio.sleep(5)  # Wait before retrying

def start_consumer(cluster_id, websocket_uri):
    """Start the Kafka consumer and broadcast messages to a persistent WebSocket connection."""
    consumer = KafkaConsumer(
        'processed_emoji_data',
        bootstrap_servers='localhost:9092',
        group_id=cluster_id,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    asyncio.run(persistent_websocket_connection(websocket_uri, consumer))

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 cluster_publisher.py <cluster_id> <websocket_host> <websocket_port>")
        sys.exit(1)

    cluster_id = sys.argv[1]
    websocket_host = sys.argv[2]
    websocket_port = int(sys.argv[3])
    websocket_uri = f"ws://{websocket_host}:{websocket_port}"
    print(f"Connecting to WebSocket server at {websocket_uri}")
    start_consumer(cluster_id, websocket_uri)

if __name__ == "__main__":
    main()

