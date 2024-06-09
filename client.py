import argparse
import json
import logging
import asyncio
from network import NetworkClient
from task_executor import TaskExecutor

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser(description="XRP Cloud Function Client")
    parser.add_argument('--host', type=str, required=True, help='Server host address')
    parser.add_argument('--port', type=int, required=True, help='Server port')
    return parser.parse_args()

async def main(host, port):
    # Initialize network client
    network_client = NetworkClient(host, port)
    await network_client.connect()

    wallet_details = {
        "public_key": 'rhsWsQjGv6sSVnRPwG1gEFkiDAaqCzhGzp',
        "private_key": 'sEd7QY4P5x4oHyXMX8eYvPp49fMERAX',
    }
    
    # Send wallet details to server
    await network_client.send_data(json.dumps({"wallet_details": wallet_details}))
    
    # Initialize task executor
    task_executor = TaskExecutor()
    
    async def receive_and_execute_tasks():
        while True:
            # Receive task from server
            task_data = await network_client.receive_data()
            if task_data:
                task = json.loads(task_data)
                lua_code = task['lua_code']
                
                # Execute Lua code
                result = task_executor.execute_lua_code(lua_code)
                
                # Send result back to server
                result_data = json.dumps({'task_id': task['task_id'], 'result': result})
                await network_client.send_data(result_data)
    
    try:
        await asyncio.gather(
            receive_and_execute_tasks()
        )
    except KeyboardInterrupt:
        pass
    finally:
        await network_client.close()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.host, args.port))
