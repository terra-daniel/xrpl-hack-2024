import asyncio
import websockets

class NetworkClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.uri = f"ws://{self.host}:{self.port}/ws"
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        print("Connected to the server")

    async def send_data(self, data):
        await self.websocket.send(data)
        print(f"Sent data: {data}")

    async def receive_data(self):
        data = await self.websocket.recv()
        print(f"Received data: {data}")
        return data

    async def close(self):
        await self.websocket.close()
        print("Connection closed")
