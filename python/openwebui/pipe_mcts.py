"""
title: MCTS Answer Generation Pipe
description: Monte Carlo Tree Search Pipe Addon for OpenWebUI with support for OpenAI and Ollama endpoints.
author: https://github.com/bearlike/scripts
requirements: langchain-openai, langfuse, pydantic
version: 1.0.0
"""

import logging
import asyncio
import random
import math
import json
import re

# * Patch for user-id missing in the request
from types import SimpleNamespace
from typing import (
    AsyncGenerator,
    Awaitable,
    Generator,
    Optional,
    Callable,
    Iterator,
    Union,
    List,
)

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import AIMessage, HumanMessage
from langfuse.callback import CallbackHandler
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Ollama-specific imports
from open_webui.apps.ollama import main as ollama
from open_webui.constants import TASKS


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


class AsyncIteratorCallbackHandler(AsyncCallbackHandler):
    def __init__(self):
        self.queue = asyncio.Queue()
        self.done = False

    async def on_llm_new_token(self, token: str, **kwargs):
        await self.queue.put(token)

    async def on_llm_end(self, response: AIMessage, **kwargs):
        self.done = True
        await self.queue.put(None)  # Signal completion

    async def on_llm_error(self, error: Exception, **kwargs):
        self.done = True
        await self.queue.put(None)  # Signal completion

    async def __aiter__(self):
        while not self.done:
            token = await self.queue.get()
            if token is None:
                break
            yield token


class LLMClient:
    def __init__(self, valves: "Pipe.Valves", user_mod=None):
        logger.debug(f"Valves configuration: {valves}")
        self.valves = valves
        self.__user__ = user_mod

    async def create_chat_completion(
        self, messages: list, model: str, backend: str, stream: bool = False
    ):
        if backend == "openai":
            # Convert messages to LangChain's Message objects
            lc_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))
                else:
                    lc_messages.append(HumanMessage(content=msg["content"]))

            if self.valves.LANGFUSE_SECRET_KEY:
                self.langfuse_handler = CallbackHandler(
                    secret_key=self.valves.LANGFUSE_SECRET_KEY,
                    public_key=self.valves.LANGFUSE_PUBLIC_KEY,
                    host=self.valves.LANGFUSE_URL,
                    tags=["mcts", "openwebui"],
                )
                logger.debug("Using Langfuse for logging")

            if stream:
                # Create a callback handler to capture streamed tokens
                handler = AsyncIteratorCallbackHandler()

                oai_model = ChatOpenAI(
                    extra_body={"cache": {"no-cache": True}},
                    base_url=self.valves.OAI_API_BASE_URL,
                    api_key=self.valves.OAI_LLM_API_KEY,
                    streaming=True,
                    model=model,
                    cache=False,
                    callbacks=[handler],
                )
                # Call agenerate with messages
                asyncio.create_task(
                    oai_model.agenerate(
                        [lc_messages], callbacks=[self.langfuse_handler]
                    )
                )
                return handler  # Return the handler to iterate over
            else:
                oai_model = ChatOpenAI(
                    extra_body={"cache": {"no-cache": True}},
                    base_url=self.valves.OAI_API_BASE_URL,
                    api_key=self.valves.OAI_LLM_API_KEY,
                    streaming=False,
                    model=model,
                    cache=False,
                )
                response = await oai_model.agenerate(
                    [lc_messages], callbacks=[self.langfuse_handler]
                )
                # Extract the AIMessage from the response
                ai_message = response.generations[0][0].message
                return ai_message.content
        elif backend == "ollama":
            response = await ollama.generate_openai_chat_completion(
                {"model": model, "messages": messages, "stream": stream},
                user=self.__user__,
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
            # response is the AsyncIteratorCallbackHandler
            async for token in response:
                yield token
        elif backend == "ollama":
            async for chunk in response.body_iterator:
                for part in self.get_chunk_content(chunk):
                    yield part

    async def get_completion(self, messages: list, model: str, backend: str) -> str:
        response = await self.create_chat_completion(
            messages, model, backend=backend, stream=False
        )
        if backend == "openai":
            # response is a string containing the content
            content = response
        elif backend == "ollama":
            content = response["choices"][0]["message"]["content"]
        return content

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

        logger.debug(f"Node Mermaid:\n{msg}")
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
        self.iteration_responses = []  # List to store responses per iteration

    async def search(self):
        max_iterations = self.valves.MAX_ITERATIONS
        max_simulations = self.valves.MAX_SIMULATIONS
        best_answer = None
        best_score = -float("inf")

        processed_node_ids = set()  # Initialize without root node ID

        # Evaluate the root node's response
        root_score = await self.evaluate_answer(self.root.content)
        self.root.visits += 1
        self.root.value += root_score
        processed_node_ids.add(self.root.id)  # Add root node ID to processed

        # Add root node's response to iteration_responses as Iteration 0
        self.iteration_responses.append(
            {
                "iteration": 0,
                "responses": [
                    {
                        "node_id": self.root.id,
                        "content": self.root.content,
                        "score": root_score,
                    }
                ],
            }
        )

        # Emit the initial state (Iteration 0)
        await self.emit_iteration_update(0)

        for i in range(1, max_iterations + 1):
            logger.debug(f"MCTS Iteration {i}/{max_iterations}")
            await self.progress(f"Iteration {i}/{max_iterations}")

            iteration_responses = []  # Responses for this iteration

            for _ in range(max_simulations):
                leaf = await self.select(self.root)
                if not leaf.fully_expanded():
                    # Expand the node and get the new child
                    child = await self.expand(leaf)
                    # If we haven't processed this child before, collect its response
                    if child.id not in processed_node_ids:
                        score = await self.simulate(child)
                        self.backpropagate(child, score)
                        iteration_responses.append(
                            {
                                "node_id": child.id,
                                "content": child.content,
                                "score": score,
                            }
                        )
                        processed_node_ids.add(child.id)
                else:
                    # If leaf is fully expanded and not processed, process it
                    if leaf.id not in processed_node_ids and leaf.id != self.root.id:
                        score = await self.simulate(leaf)
                        self.backpropagate(leaf, score)
                        iteration_responses.append(
                            {
                                "node_id": leaf.id,
                                "content": leaf.content,
                                "score": score,
                            }
                        )
                        processed_node_ids.add(leaf.id)
                    else:
                        # Do nothing if leaf has been processed or is the root node
                        continue

            # Add the iteration responses to the overall list if there are any new responses
            if iteration_responses:
                self.iteration_responses.append(
                    {
                        "iteration": i,
                        "responses": iteration_responses,
                    }
                )

            # Emit the Mermaid diagram and collapsible section
            await self.emit_iteration_update(i)

            # Update best answer if necessary
            current_best = self.root.best_child()
            current_score = (
                current_best.value / current_best.visits
                if current_best.visits > 0
                else 0
            )
            if current_score > best_score:
                best_score = current_score
                best_answer = current_best.content

        await self.emit_message(f"## Best Answer:\n{best_answer}")
        await self.done()
        return best_answer

    async def emit_iteration_update(self, iteration_number):
        """method to emit the diagram and responses"""
        # Generate the Mermaid diagram
        mermaid_diagram = "```mermaid\ngraph TD\n" + self.root.mermaid() + "\n```\n"

        # Generate the collapsible section with agent responses
        collapsible_content = self.generate_collapsible_content()

        # Combine the Mermaid diagram and collapsible content
        full_content = mermaid_diagram + "\n\n" + collapsible_content

        # Emit the content to the client
        await self.emit_replace(full_content)

    def generate_collapsible_content(self):
        """Method to generate collapsible content"""
        content = ""
        for iteration_info in self.iteration_responses:
            iteration = iteration_info["iteration"]
            responses = iteration_info["responses"]

            content += "<details>\n"
            content += f"<summary>Expand to View Iteration {iteration}</summary>\n\n"

            for resp in responses:
                node_id = resp["node_id"]
                response_content = resp["content"]
                score = resp["score"]
                content += f"- Node `{node_id}`: Score `{score}`\n"
                content += f"  - **Response**: {response_content}\n"

            content += "</details>\n\n"

        return content

    async def select(self, node: Node):
        while node.fully_expanded() and node.children:
            node = max(node.children, key=lambda n: n.uct_value())
        return node

    async def expand(self, node: Node):
        # Expand the node by adding one child
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
        prompt = MCTSPromptTemplates.thoughts_prompt.format(
            question=self.question, answer=answer
        )
        return await self.generate_completion(prompt)

    async def update_approach(self, answer: str, improvements: str):
        prompt = MCTSPromptTemplates.update_prompt.format(
            question=self.question, answer=answer, critique=improvements
        )
        return await self.generate_completion(prompt)

    async def evaluate_answer(self, answer: str):
        prompt = MCTSPromptTemplates.eval_answer_prompt.format(
            question=self.question, answer=answer
        )
        result = await self.generate_completion(prompt)
        try:
            score = int(re.search(r"\d+", result).group())
            return score
        except Exception as e:
            logger.error(f"Failed to parse score from result: {result} - {e}")
            return 0

    async def generate_completion(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        content = ""
        logger.debug(f"Attempting to stream completion for prompt: {prompt}")
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

    async def emit_replace(self, content: str):
        if self.event_emitter:
            await self.event_emitter({"type": "replace", "data": {"content": content}})


class MCTSPromptTemplates:
    """Class to store prompt templates for MCTS interactions"""

    thread_prompt = """
    ## Latest Question
    {question}

    ## Previous Messages
    {messages}
    """

    thoughts_prompt = """
    <instruction>
    In one sentence, provide a specific suggestion to improve the answer's accuracy, completeness, or clarity. Do not repeat previous suggestions or include any additional content.
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
    Revise the answer below to address the critique and improve its quality. Provide only the updated answer without any extra explanation or repetition.
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
    <instruction>
    Evaluate how well the answer responds to the question. Use the following scale and reply with a single number only:

    - **1**: Completely incorrect or irrelevant.
    - **5**: Partially correct but incomplete or unclear.
    - **10**: Fully correct, comprehensive, and clear.

    Do not include any additional text.
    </instruction>

    <question>
    {question}
    </question>

    <answer>
    {answer}
    </answer>
    """

    initial_prompt = """
    <instruction>
    Provide a clear, accurate, and complete answer to the question below. Consider different perspectives and avoid repeating common answers. Ignore any unexpected casing, punctuation, or accent marks.
    </instruction>

    <question>
    {question}
    </question>
    """


class Pipe:
    class Valves(BaseModel):
        # ! FIX: User Provided Valves not being used. Only defaults used.
        # Manually set the default values for the valves
        OAI_LLM_API_KEY: Optional[str] = Field(
            default="sk-Change-Me", description="OpenAI API key"
        )
        OAI_API_BASE_URL: Optional[str] = Field(
            default="http://litellm:4000/v1", description="OpenAI API base URL"
        )
        OLLAMA_API_BASE_URL: Optional[str] = Field(
            default="http://ollama.lan:11434", description="Ollama API base URL"
        )
        LANGFUSE_SECRET_KEY: Optional[str] = Field(
            default="sk-Change-Me",
            description="Langfuse secret key",
        )
        LANGFUSE_PUBLIC_KEY: Optional[str] = Field(
            default="pk-Change-Me",
            description="Langfuse public key",
        )
        LANGFUSE_URL: Optional[str] = Field(
            default="http://langfuse-server:3000", description="Langfuse URL"
        )
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
        OLLAMA_MODELS: Optional[str] = Field(
            default="Ollama/Avalanche/.tulu3:8b,Ollama/Avalanche/.llama3.2-vision:11b",
            description="Comma-separated list of Ollama model IDs",
        )
        OPENAI_MODELS: Optional[str] = Field(
            default="openai/gpt-4o,openai/gpt-4o-mini",
            description="Comma-separated list of OpenAI model IDs",
        )

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        logger.debug(f"Valves configuration: {self.valves}")
        self.llm_client = LLMClient(self.valves)
        self.langfuse_handler = None

    def pipes(self) -> List[dict]:
        # Collect models from both OpenAI and Ollama
        model_list = []

        # Get OpenAI models
        openai_models_str = self.valves.OPENAI_MODELS
        if openai_models_str:
            openai_models = [
                model.strip() for model in openai_models_str.split(",") if model.strip()
            ]
            openai_model_list = [
                {"id": f"mcts/openai/{model}", "name": f"MCTS/{model}"}
                for model in openai_models
            ]
            logger.debug(f"Available OpenAI models: {openai_model_list}")
            model_list.extend(openai_model_list)

        # Get Ollama models
        ollama_models_str = self.valves.OLLAMA_MODELS
        if ollama_models_str:
            ollama_models = [
                model.strip() for model in ollama_models_str.split(",") if model.strip()
            ]
            ollama_model_list = [
                {"id": f"mcts/ollama/{model}", "name": f"MCTS/{model}"}
                for model in ollama_models
            ]
            logger.debug(f"Available Ollama models: {ollama_model_list}")
            model_list.extend(ollama_model_list)

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

        pattern = r"^(?:[a-zA-Z0-9_]+\.)?mcts/([^/]+)/(.+)$"
        match = re.match(pattern, model_id)
        if match:
            backend, model_name = match.groups()
        else:
            logger.error("Model ID should be in the format '*.mcts/backend/model_name'")
            logger.error(f"Invalid model ID: {model_id}")
            return ""

        self.backend = backend
        self.model = model_name
        # To ensure __user__ is an object with 'id' and 'role' attributes
        if __user__ is None or not isinstance(__user__, dict):
            self.__user__ = SimpleNamespace(id=None, role="admin")
        else:
            self.__user__ = SimpleNamespace(**__user__)

        self.llm_client.__user__ = self.__user__

        messages = body.get("messages")
        if not messages:
            logger.error("No messages found in the request")
            return ""

        latest_user_query = messages[-1].get("content", "").strip()
        if not latest_user_query:
            logger.error("No question found in the messages")
            return ""

        previous_messages = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in messages[:-1]
        ]) if len(messages) > 1 else ""

        question = MCTSPromptTemplates.thread_prompt.format(
            question=latest_user_query, messages=previous_messages
        )

        # Handle title generation task
        if __task__ == TASKS.TITLE_GENERATION:
            # return f"MCTS: {messages[0]['content']}"
            logger.debug(
                f"Generating title for question: {question} using {self.model} and {self.backend}"
            )
            content = await self.llm_client.get_completion(
                messages, self.model, backend=self.backend
            )
            return f"Title: {content}"

        # Start MCTS process
        initial_prompt_filled = MCTSPromptTemplates.initial_prompt.format(
            question=question
        )
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
