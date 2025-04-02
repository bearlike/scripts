"""
title: OpenAI ReAct + Langfuse
description: OpenAI ReAct agent using existing tools, with streaming and citations. Implemented with LangGraph.
requirements: langchain-openai, langgraph, langfuse
author: https://github.com/bearlike/scripts
version: 0.6.0
licence: MIT
"""

from typing import Callable, AsyncGenerator, Awaitable, Optional, Protocol
import os

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
from langfuse.callback import CallbackHandler
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from openai import OpenAI

BAD_NAMES = ["202", "13", "3.5", "chatgpt"]
EmitterType = Optional[Callable[[dict], Awaitable[None]]]


class SendCitationType(Protocol):
    def __call__(self, url: str, title: str,
                 content: str) -> Awaitable[None]: ...


class SendStatusType(Protocol):
    def __call__(self, status_message: str, done: bool) -> Awaitable[None]: ...


def get_send_citation(__event_emitter__: EmitterType) -> SendCitationType:
    async def send_citation(url: str, title: str, content: str):
        if __event_emitter__ is None:
            return
        await __event_emitter__(
            {
                "type": "citation",
                "data": {
                    "document": [content],
                    "metadata": [{"source": url, "html": False}],
                    "source": {"name": title},
                },
            }
        )

    return send_citation


def get_send_status(__event_emitter__: EmitterType) -> SendStatusType:
    async def send_status(status_message: str, done: bool):
        if __event_emitter__ is None:
            return
        await __event_emitter__(
            {
                "type": "status",
                "data": {"description": status_message, "done": done},
            }
        )

    return send_status


class Pipe:
    class Valves(BaseModel):
        OPENAI_BASE_URL: str = Field(
            default="http://litellm:4000/v1",
            description="Base URL for OpenAI API endpoints",
        )
        OPENAI_API_KEY: str = Field(
            default="sk-CHANGE-ME", description="OpenAI API key"
        )
        LANGFUSE_SECRET_KEY: str = Field(
            default="sk-lf-CHANGE-ME",
            description="Langfuse secret key",
        )
        LANGFUSE_PUBLIC_KEY: str = Field(
            default="pk-lf-CHANGE-ME",
            description="Langfuse public key",
        )
        LANGFUSE_URL: str = Field(
            default="http://langfuse-server:3000", description="Langfuse URL"
        )
        MODEL_PREFIX: str = Field(
            default="ReAct", description="Prefix before model ID")

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        print(f"{self.valves=}")

    def pipes(self) -> list[dict[str, str]]:
        try:
            self.setup()
        except Exception as e:
            return [{"id": "error", "name": f"Error: {e}"}]
        openai = OpenAI(**self.openai_kwargs)  # type: ignore
        models = [m.id for m in openai.models.list().data]
        models = [m for m in models if "gpt" in m or "o1-" in m]
        models = [m for m in models if not any(bad in m for bad in BAD_NAMES)]
        return [{"id": m, "name": f"{self.valves.MODEL_PREFIX}/{m}"} for m in models]

    def setup(self):
        v = self.valves
        if not v.OPENAI_API_KEY or not v.OPENAI_BASE_URL:
            raise Exception(
                "Error: OPENAI_API_KEY or OPENAI_BASE_URL is not set")
        self.openai_kwargs = {
            "base_url": v.OPENAI_BASE_URL,
            "api_key": v.OPENAI_API_KEY,
        }
        lf = (v.LANGFUSE_SECRET_KEY, v.LANGFUSE_PUBLIC_KEY, v.LANGFUSE_URL)
        if not all(lf):
            self.langfuse_kwargs = None
        else:
            self.langfuse_kwargs = {
                "secret_key": v.LANGFUSE_SECRET_KEY,
                "public_key": v.LANGFUSE_PUBLIC_KEY,
                "host": v.LANGFUSE_URL,
            }

    async def pipe(
        self,
        body: dict,
        __user__: dict | None,
        __task__: str | None,
        __tools__: dict[str, dict] | None,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None,
    ) -> AsyncGenerator:
        print(__task__)
        print(f"{__tools__=}")
        if __task__ == "function_calling":
            return

        self.setup()

        model_id = body["model"][body["model"].rfind(".") + 1:]
        model = ChatOpenAI(model=model_id, **
                           self.openai_kwargs)  # type: ignore
        if self.langfuse_kwargs:
            user_kwargs = {"user_id": __user__["id"]} if __user__ else {}
            callback_kwargs = self.langfuse_kwargs | user_kwargs
            callbacks = [CallbackHandler(**callback_kwargs)]  # type: ignore
        else:
            callbacks = []
        config = {"callbacks": callbacks}  # type: ignore

        if __task__ == "title_generation":
            content = model.invoke(body["messages"], config=config).content
            assert isinstance(content, str)
            yield content
            return

        if not __tools__:
            async for chunk in model.astream(body["messages"], config=config):
                content = chunk.content
                assert isinstance(content, str)
                yield content
            return

        send_citation = get_send_citation(__event_emitter__)
        send_status = get_send_status(__event_emitter__)

        tools = []
        for key, value in __tools__.items():
            tools.append(
                StructuredTool(
                    func=None,
                    name=key,
                    coroutine=value["callable"],
                    args_schema=value["pydantic_model"],
                    description=value["spec"]["description"],
                )
            )
        graph = create_react_agent(model, tools=tools)
        inputs = {"messages": body["messages"]}
        num_tool_calls = 0
        # type: ignore
        async for event in graph.astream_events(inputs, version="v2", config=config):
            kind = event["event"]
            data = event["data"]
            if kind == "on_chat_model_stream":
                if "chunk" in data and (content := data["chunk"].content):
                    yield content
            elif kind == "on_tool_start":
                yield "\n"
                await send_status(f"Running tool {event['name']}", False)
            elif kind == "on_tool_end":
                num_tool_calls += 1
                await send_status(
                    f"Tool '{event['name']}' returned {data.get('output')}", True
                )
                await send_citation(
                    url=f"Tool call {num_tool_calls}",
                    title=event["name"],
                    content=f"Tool '{event['name']}' with inputs {data.get('input')} returned {data.get('output')}",
                )
