"""
title: MCTS Answer Generation Pipe
author: https://github.com/bearlike/scripts
description: Monte Carlo Tree Search Pipe Addon for OpenWebUI with support for OpenAI and Ollama endpoints.
version: 1.0.0
"""

import logging
import random
import math
import asyncio
import json
import re
import os

from typing import (
    List,
    Optional,
    Callable,
    Awaitable,
    Union,
    AsyncGenerator,
    Generator,
    Iterator,
)
from pydantic import BaseModel, Field
from open_webui.constants import TASKS
from open_webui.apps.ollama import main as ollama
from types import SimpleNamespace

# Import Langfuse for logging/tracing (optional)

try:
    from langfuse.callback import CallbackHandler
except ImportError:
    CallbackHandler = None  # Langfuse is optional

# =============================================================================

# Setup Logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.set_name("mcts")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

# =============================================================================

# LLM Client


class LLMClient:
    def __init__(self, valves: "Pipe.Valves"):
        self.openai_api_key = valves.OPENAI_API_KEY
        self.openai_api_base_url = valves.OPENAI_API_BASE_URL
        self.ollama_api_base_url = valves.OLLAMA_API_BASE_URL

    async def create_chat_completion(
        self, messages: list, model: str, backend: str, stream: bool = False
    ):
        if backend == "openai":
            import openai

            openai.api_key = self.openai_api_key
            openai.api_base = self.openai_api_base_url
            # ! FIX: ChatCompletion is no longer supported
            response = await openai.ChatCompletion.acreate(
                model=model, messages=messages, stream=stream
            )
            return response
        elif backend == "ollama":
            response = await ollama.generate_openai_chat_completion(
                {"model": model, "messages": messages, "stream": stream}
            )
            return response
        else:
            raise ValueError(f"Unknown backend: {backend}")

    async def get_streaming_completion(
        self, messages: list, model: str, backend: str
    ) -> AsyncGenerator[str, None]:
        response = await self.create_chat_completion(
            messages, model, backend=backend, stream=True
        )
        if backend == "openai":
            async for chunk in response:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]
        elif backend == "ollama":
            async for chunk in response.body_iterator:
                for part in self.get_chunk_content(chunk):
                    yield part

    async def get_completion(self, messages: list, model: str, backend: str) -> str:
        response = await self.create_chat_completion(
            messages, model, backend=backend, stream=False
        )
        if backend == "openai":
            return response.choices[0].message.content
        elif backend == "ollama":
            return response["choices"][0]["message"]["content"]

    def get_chunk_content(self, chunk):
        # For Ollama only
        chunk_str = chunk.decode("utf-8")
        if chunk_str.startswith("data: "):
            chunk_str = chunk_str[6:]

        chunk_str = chunk_str.strip()

        if chunk_str == "[DONE]" or not chunk_str:
            return

        try:
            chunk_data = json.loads(chunk_str)
            if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                delta = chunk_data["choices"][0].get("delta", {})
                if "content" in delta:
                    yield delta["content"]
        except json.JSONDecodeError:
            logger.error(f'ChunkDecodeError: unable to parse "{chunk_str[:100]}"')


# =============================================================================

# MCTS Classes


class Node:
    def __init__(
        self,
        content: str,
        parent: Optional["Node"] = None,
        exploration_weight: float = 1.414,
        max_children: int = 2,
    ):
        self.id = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=4))
        self.content = content
        self.parent = parent
        self.exploration_weight = exploration_weight
        self.max_children = max_children
        self.children = []
        self.visits = 0
        self.value = 0.0

    def add_child(self, child: "Node"):
        child.parent = self
        self.children.append(child)

    def fully_expanded(self):
        return len(self.children) >= self.max_children

    def uct_value(self):
        epsilon = 1e-6
        if self.visits == 0:
            return float("inf")
        return self.value / self.visits + self.exploration_weight * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

    def best_child(self):
        if not self.children:
            return self
        return max(self.children, key=lambda child: child.visits).best_child()

    def mermaid(self, offset=0, selected=None):
        padding = " " * offset
        content_preview = self.content.replace('"', "").replace("\n", " ")[:25]
        msg = f"{padding}{self.id}[{self.id}:{self.visits} - {content_preview}]\n"

        if selected == self.id:
            msg += f"{padding}style {self.id} stroke:#0ff\n"

        for child in self.children:
            msg += child.mermaid(offset + 4, selected)
            msg += f"{padding}{self.id} --> {child.id}\n"

        return msg


class MCTSAgent:
    def __init__(
        self,
        root_content: str,
        llm_client: LLMClient,
        question: str,
        event_emitter: Callable[[dict], Awaitable[None]],
        valves: "Pipe.Valves",
        model: str,
        backend: str,
    ):
        self.root = Node(content=root_content)
        self.question = question
        self.llm_client = llm_client
        self.event_emitter = event_emitter
        self.valves = valves
        self.selected = None
        self.model = model
        self.backend = backend

    async def search(self):
        max_iterations = self.valves.MAX_ITERATIONS
        max_simulations = self.valves.MAX_SIMULATIONS
        best_answer = None
        best_score = -float("inf")

        for i in range(max_iterations):
            logger.debug(f"MCTS Iteration {i+1}/{max_iterations}")
            await self.progress(f"Iteration {i+1}/{max_iterations}")

            for _ in range(max_simulations):
                leaf = await self.select(self.root)
                if not leaf.fully_expanded():
                    leaf = await self.expand(leaf)
                score = await self.simulate(leaf)
                self.backpropagate(leaf, score)

            current_best = self.root.best_child()
            current_score = (
                current_best.value / current_best.visits
                if current_best.visits > 0
                else 0
            )
            if current_score > best_score:
                best_score = current_score
                best_answer = current_best.content

        await self.emit_message(f"Best Answer:\n{best_answer}")
        await self.done()
        return best_answer

    async def select(self, node: Node):
        while node.fully_expanded() and node.children:
            node = max(node.children, key=lambda n: n.uct_value())
        return node

    async def expand(self, node: Node):
        thought = await self.generate_thought(node.content)
        new_content = await self.update_approach(node.content, thought)
        child = Node(
            content=new_content,
            parent=node,
            exploration_weight=self.valves.EXPLORATION_WEIGHT,
            max_children=self.valves.MAX_CHILDREN,
        )
        node.add_child(child)
        return child

    async def simulate(self, node: Node):
        score = await self.evaluate_answer(node.content)
        return score

    def backpropagate(self, node: Node, score: float):
        while node is not None:
            node.visits += 1
            node.value += score
            node = node.parent

    # LLM interaction methods
    async def generate_thought(self, answer: str):
        prompt = thoughts_prompt.format(question=self.question, answer=answer)
        return await self.generate_completion(prompt)

    async def update_approach(self, answer: str, improvements: str):
        prompt = update_prompt.format(
            question=self.question, answer=answer, critique=improvements
        )
        return await self.generate_completion(prompt)

    async def evaluate_answer(self, answer: str):
        prompt = eval_answer_prompt.format(question=self.question, answer=answer)
        result = await self.generate_completion(prompt)
        try:
            score = int(re.search(r"\d+", result).group())
            return score
        except Exception as e:
            logger.error(f"Failed to parse score from result: {result}")
            return 0

    async def generate_completion(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        content = ""
        async for chunk in self.llm_client.get_streaming_completion(
            messages, model=self.model, backend=self.backend
        ):
            content += chunk
            await self.emit_message(chunk)
        return content

    # Event emitter methods
    async def progress(self, message: str):
        await self.emit_status("info", message, False)

    async def done(self):
        await self.emit_status("info", "Done", True)

    async def emit_message(self, message: str):
        if self.event_emitter:
            await self.event_emitter({"type": "message", "data": {"content": message}})

    async def emit_status(self, level: str, message: str, done: bool):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "level": level,
                        "description": message,
                        "done": done,
                    },
                }
            )


# =============================================================================

# Prompts

thoughts_prompt = """
<instruction>
Give a suggestion on how this answer can be improved.
WRITE ONLY AN IMPROVEMENT SUGGESTION AND NOTHING ELSE.
YOUR REPLY SHOULD BE A SINGLE SENTENCE.
</instruction>

<question>
{question}
</question>

<draft>
{answer}
</draft>
"""

update_prompt = """
<instruction>
Your task is to read the question and the answer below, then analyze the given critique.
When you are done - think about how the answer can be improved based on the critique.
WRITE A REVISED ANSWER THAT ADDRESSES THE CRITIQUE. DO NOT WRITE ANYTHING ELSE.
</instruction>
<question>
{question}
</question>
<draft>
{answer}
</draft>
<critique>
{critique}
</critique>
"""

eval_answer_prompt = """
Given the following text:
"{answer}"

How well does it answer this question:
"{question}"

Rate the answer from 1 to 10, where 1 is completely wrong or irrelevant and 10 is a perfect answer.
Reply with a single number between 1 and 10 only. Do not write anything else, it will be discarded.
"""

initial_prompt = """
<instruction>
Answer the question below. Do not pay attention to unexpected casing, punctuation, or accent marks.
</instruction>

<question>
{question}
</question>
"""

# =============================================================================

# Pipe Class


class Pipe:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
        OPENAI_API_BASE_URL: str = Field(
            default="https://api.openai.com/v1", description="OpenAI API base URL"
        )
        OLLAMA_API_BASE_URL: str = Field(
            default="http://avalanche.lan:11434", description="Ollama API base URL"
        )
        USE_OPENAI: bool = Field(
            default=True, description="Whether to use OpenAI endpoints"
        )
        LANGFUSE_SECRET_KEY: str = Field(default="", description="Langfuse secret key")
        LANGFUSE_PUBLIC_KEY: str = Field(default="", description="Langfuse public key")
        LANGFUSE_URL: str = Field(default="", description="Langfuse URL")
        EXPLORATION_WEIGHT: float = Field(
            default=1.414, description="Exploration weight for MCTS"
        )
        MAX_ITERATIONS: int = Field(
            default=2, description="Maximum iterations for MCTS"
        )
        MAX_SIMULATIONS: int = Field(
            default=2, description="Maximum simulations for MCTS"
        )
        MAX_CHILDREN: int = Field(
            default=2, description="Maximum number of children per node in MCTS"
        )
        OLLAMA_MODELS: str = Field(
            default="Ollama/Avalanche/.tulu3:8b,Ollama/Avalanche/.llama3.2-vision:11b",
            description="Comma-separated list of Ollama model IDs",
        )
        OPENAI_MODELS: str = Field(
            default="openai/gpt-4o,openai/gpt-4o-mini",
            description="Comma-separated list of OpenAI model IDs",
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        logger.debug(f"Valves configuration: {self.valves}")
        self.llm_client = LLMClient(self.valves)
        self.langfuse_handler = None
        if (
            self.valves.LANGFUSE_SECRET_KEY
            and self.valves.LANGFUSE_PUBLIC_KEY
            and self.valves.LANGFUSE_URL
            and CallbackHandler
        ):
            self.langfuse_handler = CallbackHandler(
                secret_key=self.valves.LANGFUSE_SECRET_KEY,
                public_key=self.valves.LANGFUSE_PUBLIC_KEY,
                host=self.valves.LANGFUSE_URL,
            )

    def pipes(self) -> List[dict]:
        # Hardcode models from valves
        if self.valves.USE_OPENAI:
            openai_models_str = self.valves.OPENAI_MODELS
            openai_models = [
                model.strip() for model in openai_models_str.split(",") if model.strip()
            ]
            model_list = [
                {"id": f"mcts/openai/{model}", "name": f"MCTS/{model}"}
                for model in openai_models
            ]
            logger.debug(f"Available OpenAI models: {model_list}")
            return model_list
        else:
            ollama_models_str = self.valves.OLLAMA_MODELS
            ollama_models = [
                model.strip() for model in ollama_models_str.split(",") if model.strip()
            ]
            model_list = [
                {"id": f"mcts/ollama/{model}", "name": f"MCTS/{model}"}
                for model in ollama_models
            ]
            logger.debug(f"Available Ollama models: {model_list}")
            return model_list

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__=None,
        __task__=None,
    ) -> Union[str, Generator, Iterator]:
        # Resolve model and question from the body
        model_id = body.get("model")
        if not model_id:
            logger.error("No model specified in the request")
            return ""

        pattern = r'^(?:[a-zA-Z0-9_]+\.)?mcts/([^/]+)/(.+)$'
        match = re.match(pattern, model_id)
        if match:
            backend, model_name = match.groups()
        else:
            logger.error("Model ID should be in the format '*.mcts/backend/model_name'")
            logger.error(f"Invalid model ID: {model_id}")
            return ""

        self.backend = backend
        self.model = model_name

        messages = body.get("messages")
        if not messages:
            logger.error("No messages found in the request")
            return ""

        question = messages[-1].get("content", "").strip()
        if not question:
            logger.error("No question found in the messages")
            return ""

        # Handle title generation task
        if __task__ == TASKS.TITLE_GENERATION:
            logger.debug(f"Generating title for question: {question} using {self.model} and {self.backend}")
            content = await self.llm_client.get_completion(
                messages, self.model, backend=self.backend
            )
            return f"Title: {content}"

        # Start MCTS process
        initial_prompt_filled = initial_prompt.format(question=question)
        initial_reply = await self.llm_client.get_completion(
            [{"role": "user", "content": initial_prompt_filled}],
            self.model,
            backend=self.backend,
        )

        # Create MCTS agent
        mcts_agent = MCTSAgent(
            root_content=initial_reply,
            llm_client=self.llm_client,
            question=question,
            event_emitter=__event_emitter__,
            valves=self.valves,
            model=self.model,
            backend=self.backend,
        )

        # Run MCTS search
        best_answer = await mcts_agent.search()

        return ""
