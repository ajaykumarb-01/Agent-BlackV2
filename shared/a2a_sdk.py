import inspect
import json
import logging
import time
from typing import Any, Awaitable, Callable

import httpx
from fastapi import FastAPI

logger = logging.getLogger("a2a_sdk")

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import (
    get_artifact_text,
    get_stream_response_text,
    new_text_message,
    new_text_part,
    new_task_from_user_message,
)
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types.a2a_pb2 import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
)
from a2a.utils.constants import PROTOCOL_VERSION_1_0


A2A_CARD_PATH = "/.well-known/agent-card.json"
A2A_RPC_PATH = "/a2a"
TEXT_MODE = "text/plain"


def build_agent_card(
    *,
    name: str,
    description: str,
    base_url: str,
    tasks: list[str],
    streaming: bool = True,
) -> AgentCard:
    skills = [
        AgentSkill(
            id=task,
            name=task.replace("_", " ").title(),
            description=f"Performs {task.replace('_', ' ')}",
            input_modes=[TEXT_MODE],
            output_modes=[TEXT_MODE],
            tags=[task.split("_")[0], "agent-black"],
            examples=[f"Help with {task.replace('_', ' ')}"],
        )
        for task in tasks
    ]
    return AgentCard(
        name=name,
        description=description,
        version="1.0.0",
        default_input_modes=[TEXT_MODE],
        default_output_modes=[TEXT_MODE],
        capabilities=AgentCapabilities(streaming=streaming),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version=PROTOCOL_VERSION_1_0,
                url=f"{base_url.rstrip('/')}{A2A_RPC_PATH}",
            )
        ],
        skills=skills,
    )


def agent_card_to_legacy_dict(card: AgentCard) -> dict[str, Any]:
    return {
        "name": card.name,
        "description": card.description,
        "url": card.supported_interfaces[0].url if card.supported_interfaces else "",
        "version": card.version,
        "capabilities": [skill.id for skill in card.skills],
        "defaultInputModes": list(card.default_input_modes),
        "defaultOutputModes": list(card.default_output_modes),
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "inputModes": list(skill.input_modes),
                "outputModes": list(skill.output_modes),
                "tags": list(skill.tags),
                "examples": list(skill.examples),
            }
            for skill in card.skills
        ],
    }


class AsyncFunctionExecutor(AgentExecutor):
    def __init__(self, run_fn: Callable[[str], Any | Awaitable[Any]]) -> None:
        self._run_fn = run_fn

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.message:
            raise ValueError("A2A request is missing a message payload")

        task = context.current_task or new_task_from_user_message(context.message)
        if not context.current_task:
            await event_queue.enqueue_event(task)

        task_updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )
        await task_updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message(
                "Processing request...",
                media_type=TEXT_MODE,
                role=Role.ROLE_AGENT,
                context_id=task.context_id,
                task_id=task.id,
            ),
        )

        query = context.get_user_input()
        result = await _run_agent_fn(self._run_fn, query)
        await task_updater.add_artifact(
            parts=[new_text_part(text=_serialize_result(result), media_type=TEXT_MODE)],
            name="result",
            last_chunk=True,
        )
        await task_updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message(
                "Request completed",
                media_type=TEXT_MODE,
                role=Role.ROLE_AGENT,
                context_id=task.context_id,
                task_id=task.id,
            ),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id or (context.current_task.id if context.current_task else "")
        context_id = context.context_id or (context.current_task.context_id if context.current_task else "")
        if not task_id or not context_id:
            return
        task_updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
        )
        await task_updater.update_status(
            state=TaskState.TASK_STATE_CANCELED,
            message=new_text_message(
                "Task canceled",
                media_type=TEXT_MODE,
                role=Role.ROLE_AGENT,
                context_id=context_id,
                task_id=task_id,
            ),
        )


def add_sdk_a2a_routes(
    app: FastAPI,
    *,
    card: AgentCard,
    run_fn: Callable[[str], Any | Awaitable[Any]],
    rpc_path: str = A2A_RPC_PATH,
) -> None:
    request_handler = DefaultRequestHandler(
        agent_executor=AsyncFunctionExecutor(run_fn),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    for route in create_agent_card_routes(card, card_url=A2A_CARD_PATH):
        app.router.routes.append(route)
    for route in create_jsonrpc_routes(request_handler, rpc_path):
        app.router.routes.append(route)


async def send_text_task(base_url: str, query: str) -> dict[str, Any]:
    logger.info("A2A send_text_task  url=%s  payload_size=%d", base_url, len(query))
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=300) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        card = await resolver.get_agent_card()
        rpc_url = f"{base_url.rstrip('/')}{A2A_RPC_PATH}"
        if card.supported_interfaces:
            card.supported_interfaces[0].url = rpc_url
        else:
            card.supported_interfaces = [
                AgentInterface(
                    protocol_binding="JSONRPC",
                    protocol_version=PROTOCOL_VERSION_1_0,
                    url=rpc_url,
                )
            ]
        client = await create_client(
            agent=card,
            client_config=ClientConfig(streaming=True, httpx_client=httpx_client),
        )
        try:
            request = SendMessageRequest(
                message=new_text_message(query, media_type=TEXT_MODE, role=Role.ROLE_USER)
            )
            artifact_chunk = None
            message_chunk = None
            task_chunk = None
            final_chunk = None
            chunk_count = 0
            async for chunk in client.send_message(request):
                final_chunk = chunk
                chunk_count += 1
                if chunk.HasField("artifact_update") and artifact_chunk is None:
                    artifact_chunk = chunk
                elif chunk.HasField("message") and message_chunk is None:
                    message_chunk = chunk
                elif chunk.HasField("task") and task_chunk is None:
                    task_chunk = chunk

            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            chosen = artifact_chunk or message_chunk or task_chunk or final_chunk
            if chosen is None:
                logger.error(
                    "A2A no response  url=%s  chunks_received=%d  elapsed=%sms",
                    base_url,
                    chunk_count,
                    elapsed_ms,
                )
                raise RuntimeError(f"A2A agent at {base_url} returned no response")
            logger.info(
                "A2A response OK  url=%s  chunks_received=%d  elapsed=%sms  source=%s",
                base_url,
                chunk_count,
                elapsed_ms,
                "artifact" if artifact_chunk else "message" if message_chunk else "task" if task_chunk else "final",
            )
            return normalize_stream_response(chosen)
        finally:
            await client.close()


def normalize_stream_response(response) -> dict[str, Any]:
    if response.HasField("task"):
        return normalize_task(response.task)
    if response.HasField("message"):
        text = get_stream_response_text(response)
        return _parse_text_payload(text)
    if response.HasField("artifact_update"):
        text = get_stream_response_text(response)
        return _parse_text_payload(text)
    if response.HasField("status_update"):
        return {
            "status": response.status_update.status.state,
            "message": get_stream_response_text(response),
        }
    return {"raw_response": str(response)}


def normalize_task(task: Task) -> dict[str, Any]:
    texts = [get_artifact_text(artifact) for artifact in task.artifacts]
    payload = "\n".join(text for text in texts if text).strip()
    if payload:
        parsed = _parse_text_payload(payload)
        if isinstance(parsed, dict):
            return parsed
        return {"result": parsed}
    return {
        "task_id": task.id,
        "context_id": task.context_id,
        "status": task.status.state,
    }


async def _run_agent_fn(run_fn: Callable[[str], Any | Awaitable[Any]], query: str) -> Any:
    if inspect.iscoroutinefunction(run_fn):
        return await run_fn(query)
    result = run_fn(query)
    if inspect.isawaitable(result):
        return await result
    return result


def _serialize_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=True)


def _parse_text_payload(text: str) -> Any:
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"result": text}
