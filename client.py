import argparse
import json
import time
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
    
    # Initialize task executor
    task_executor = TaskExecutor()
    
    # Main loop to receive and execute tasks
    try:
        while True:
            await asyncio.sleep(1)
            logging.info('Checking for new tasks')
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
    except KeyboardInterrupt:
        pass
    finally:
        await network_client.close()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.host, args.port))
