1. server to distrubute tasks
2. server to make the smart contracts and release funds
3. server has websocket connection to clients and checks consensun of nodes.

`uvicorn server:app --host 127.0.0.1 --port 8000 --reload`

`python3 client.py --host localhost --port 8000`