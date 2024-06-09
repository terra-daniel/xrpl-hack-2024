from fastapi import FastAPI, WebSocket
import json
from xrpl.wallet import Wallet
from xrpl_utils import create_escrow, finish_escrow
import logging
from typing import Dict, List
from pydantic import BaseModel
import subprocess

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Dictionary to store tasks and results
tasks = {}

# List to store WebSocket clients and their wallet addresses
clients: List[Dict[str, WebSocket]] = []

class TaskRequest(BaseModel):
    lua_code: str
    escrow_sequence: int

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
async def create_task(request: TaskRequest):
    task_id = len(tasks) + 1
    tasks[task_id] = {"lua_code": request.lua_code, "results": [], "escrow_sequence": request.escrow_sequence}
    
    # Distribute task to connected clients
    for client in clients:
        await client['websocket'].send_text(json.dumps({"task_id": task_id, "lua_code": request.lua_code, "escrow_sequence": request.escrow_sequence}))
    
    return {"task_id": task_id, "escrow_sequence": request.escrow_sequence}

# Function to handle results from clients
async def handle_results(websocket: WebSocket, data: str):
    result = json.loads(data)
    task_id = result['task_id']
    if task_id not in tasks:
        tasks[task_id] = {'results': []}
    tasks[task_id]['results'].append(result['result'])

    async def run_javascript_code() -> str:
        try:
            # Run the JavaScript code using Node.js
            # TODO: REMOVE THIS ATROCITY AND PLACE THIS IN FRONT END
            process = subprocess.Popen(
                ['node', '-e', """
                        const xrpl = require('xrpl')
                        const { Client, Wallet } = xrpl

                        async function main () {
                            const client = new Client('wss://s.altnet.rippletest.net:51233')
                            await client.connect()

                            const wallet = Wallet.fromSecret("sEd7QY4P5x4oHyXMX8eYvPp49fMERAX")

                            // from the result of completing the task
                            const info = {
                            fulfillment: 'A022802037902991EBEF272A9BE1E600452AE4D1F8F480A722D32F507D99843EDCA15411',
                            sequence: 1354084
                            }

                            // The person who submitted the job
                            const rec = {
                            wallet_address: 'rD1pL1Kkg35WLCyWFwN9xhdBizn3Mk16vC',
                            condition: 'A0258020F7736861FADD4DB1B43493C2AD4AC21693E93F9C5BDB87C4A17AAECE38093564810120',
                            }

                            const prepared = await client.autofill({
                                "TransactionType": "EscrowFinish",
                                "Account": wallet.address,
                                "Owner": rec.wallet_address,
                                "OfferSequence": info.sequence,
                                "Condition": rec.condition,
                                "Fulfillment": info.fulfillment
                            })

                            console.log("bi")

                            const signed = wallet.sign(prepared)
                            const tx = await client.submitAndWait(signed.tx_blob)

                            console.log(tx, tx.result)

                            await client.disconnect()
                        }

                        main()
                        """],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"JavaScript execution error: {stderr.decode('utf-8')}")

            return stdout.decode('utf-8')
        except Exception as e:
            logging.error(f"Error running JavaScript code: {e}")
            return str(e)
    
    await handle_escrow(task_id)


# Function to validate results and handle escrow release
async def handle_escrow(task_id):
    # Release the escrow using the stored wallet for the client
    for client in clients:
        client_wallet = client['wallet_details']
        finish_escrow(client_wallet, client_wallet['public_key'], tasks[task_id]['escrow_sequence'])
        logging.info(f"Escrow for task {task_id} released using wallet {client_wallet['public_key']}.")
        # Notify clients about escrow release
        await client['websocket'].send_text(json.dumps({'task_id': task_id, 'status': 'escrow_released'}))
    else:
        logging.info(f"Validation failed for task {task_id}.")
