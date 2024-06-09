from fastapi import FastAPI, WebSocket
import json
from xrpl.wallet import Wallet
from xrpl_utils import create_escrow, finish_escrow
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Dictionary to store tasks and results
tasks = {}

# List to store WebSocket clients and their wallet addresses
clients: List[Dict[str, WebSocket]] = []


# WebSocket route for client connections
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_text()
    client_info = json.loads(data)
    client_wallet = client_info['wallet_details']
    clients.append({"websocket": websocket, "wallet_details": client_wallet})
    try:
        while True:
            data = await websocket.receive_text()
            await handle_results(websocket, data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.remove({"websocket": websocket, "wallet_details": client_wallet})

# Route for receiving tasks from users
@app.post("/task")
async def create_task(lua_code: str, escrow_sequence: int):
    task_id = len(tasks) + 1
    tasks[task_id] = {"lua_code": lua_code, "results": [], "escrow_sequence": escrow_sequence}
    
    # Distribute task to connected clients
    for client in clients:
        await client['websocket'].send_text(json.dumps({"task_id": task_id, "lua_code": lua_code, "escrow_sequence": escrow_sequence}))
    
    return {"task_id": task_id, "escrow_sequence": escrow_sequence}

# Function to handle results from clients
async def handle_results(websocket: WebSocket, data: str):
    result = json.loads(data)
    task_id = result['task_id']
    if task_id not in tasks:
        tasks[task_id] = {'results': []}
    tasks[task_id]['results'].append(result['result'])
    if validate_results(task_id):
        await handle_escrow(task_id)

# Function to validate results and handle escrow release
async def handle_escrow(task_id):
    if validate_results(task_id):
        # Release the escrow using the stored wallet for the client
        for client in clients:
            client_wallet = client['wallet_details']
            finish_escrow(client_wallet, client_wallet['public_key'], tasks[task_id]['escrow_sequence'])
            logging.info(f"Escrow for task {task_id} released using wallet {client_wallet['public_key']}.")
            # Notify clients about escrow release
            await client['websocket'].send_text(json.dumps({'task_id': task_id, 'status': 'escrow_released'}))
    else:
        logging.info(f"Validation failed for task {task_id}.")

# Function to validate results
def validate_results(task_id):
    results = tasks[task_id]['results']
    if len(results) > 1 and all(result == results[0] for result in results):
        return True
    return False
