from fastapi import FastAPI, WebSocket
from typing import List
import json
from xrpl.wallet import Wallet
from xrpl_utils import create_escrow, finish_escrow
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Dictionary to store tasks and results
tasks = {}

# Nodes list
clients = []

# Wallet for XRP Ledger interaction (replace with actual wallet details)
# test_wallet = Wallet(seed="yourseedhere", public_key="yourpublickeyhere", private_key="yourprivatekeyhere")

# WebSocket route for client connections
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await handle_results(websocket, data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.remove(websocket)

# WebSocket route for client connections
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    logging.info(f"Client connected: {clients}")
    try:
        while True:
            data = await websocket.receive_text()
            await handle_results(websocket, data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.remove(websocket)

# Route for receiving tasks from users
@app.post("/task")
async def create_task(lua_code: str):
    task_id = len(tasks) + 1
    tasks[task_id] = {"lua_code": lua_code}
    # Distribute task to connected clients
    for client in clients:
        await client.send_text(json.dumps({"task_id": task_id, "lua_code": lua_code}))
    return {"task_id": task_id}

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
        # Release the escrow
        finish_escrow(test_wallet, test_wallet.classic_address, tasks[task_id]['escrow_sequence'])
        print(f"Escrow for task {task_id} released.")
        # Notify clients about escrow release
        for client in clients:
            await client.send_text(json.dumps({'task_id': task_id, 'status': 'escrow_released'}))
    else:
        print(f"Validation failed for task {task_id}.")

# Function to validate results
def validate_results(task_id):
    results = tasks[task_id]['results']
    if len(results) > 1 and all(result == results[0] for result in results):
        return True
    return False
