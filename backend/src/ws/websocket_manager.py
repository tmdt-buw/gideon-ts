from fastapi import WebSocket


class WebsocketManager:

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_text(self, text: str):
        for connection in self.active_connections:
            await connection.send_text(text)

    async def send_project_update(self, project_update: str):
        for connection in self.active_connections:
            await connection.send_json(project_update)


# init websocket
manager = WebsocketManager()
