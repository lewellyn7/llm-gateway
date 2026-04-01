"""WebSocket routes for streaming responses."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
# asyncio

# verify_api_key
from app.services.llm_router import LLMRouter

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/v1/chat/stream")
async def websocket_chat(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for streaming chat completions.

    Connect with: wss://domain.com/ws/v1/chat/stream?token=sk-xxx

    Send JSON messages:
    {
        "type": "chat",
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello!"}]
    }

    Receive streaming responses as SSE-like JSON.
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    await manager.connect(websocket, client_id)

    try:
        # Authenticate
        # authenticated = True  # noqa: F841
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)

        if auth_data.get("type") == "auth":
            token = auth_data.get("token")
            if token:
                from app.core.security import verify_token

                try:
                    _ = verify_token(token)
                    await manager.send_json(websocket, {"type": "auth", "status": "ok"})
                except Exception:
                    await manager.send_json(
                        websocket,
                        {"type": "auth", "status": "error", "message": "Invalid token"},
                    )
                    return
        else:
            await manager.send_json(
                websocket, {"type": "error", "message": "Expected auth message first"}
            )
            return

        # Message handling loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "chat":
                model = message.get("model", "gpt-4o-mini")
                messages = message.get("messages", [])
                temperature = message.get("temperature", 1.0)
                max_tokens = message.get("max_tokens", 4096)

                router_svc = LLMRouter()

                try:
                    # Send "start" event
                    await manager.send_json(
                        websocket, {"type": "start", "model": model}
                    )

                    # Stream response
                    full_content = ""
                    async for chunk in router_svc.stream_chat(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ):
                        await manager.send_json(
                            websocket, {"type": "content", "content": chunk}
                        )
                        full_content += chunk

                    # Send "done" event
                    await manager.send_json(
                        websocket, {"type": "done", "content": full_content}
                    )

                except Exception as e:
                    await manager.send_json(
                        websocket, {"type": "error", "message": str(e)}
                    )

            elif message.get("type") == "ping":
                await manager.send_json(websocket, {"type": "pong"})

            elif message.get("type") == "close":
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(client_id)


@router.websocket("/v1/completions/stream")
async def websocket_completions(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for streaming text completions.
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    await manager.connect(websocket, client_id)

    try:
        # Authenticate
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)

        if auth_data.get("type") == "auth":
            token = auth_data.get("token")
            if token:
                from app.core.security import verify_token

                try:
                    _ = verify_token(token)
                    await manager.send_json(websocket, {"type": "auth", "status": "ok"})
                except Exception:
                    await manager.send_json(
                        websocket,
                        {"type": "auth", "status": "error", "message": "Invalid token"},
                    )
                    return

        # Message handling loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "complete":
                prompt = message.get("prompt", "")
                model = message.get("model", "gpt-3.5-turbo")
                max_tokens = message.get("max_tokens", 100)

                router_svc = LLMRouter()

                try:
                    await manager.send_json(websocket, {"type": "start"})

                    messages = [{"role": "user", "content": prompt}]
                    full_content = ""
                    async for chunk in router_svc.stream_chat(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                    ):
                        await manager.send_json(
                            websocket, {"type": "content", "content": chunk}
                        )
                        full_content += chunk

                    await manager.send_json(
                        websocket, {"type": "done", "content": full_content}
                    )
                except Exception as e:
                    await manager.send_json(
                        websocket, {"type": "error", "message": str(e)}
                    )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(client_id)
