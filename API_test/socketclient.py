import websocket

def on_message(_, message):
    print(f"Received message: {message}")

ws = websocket.WebSocketApp("ws://your-server-address/socket.io/?transport=websocket",
                            on_message=on_message)

ws.run_forever()
