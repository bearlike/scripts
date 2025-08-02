#!/usr/bin/env python3
"""This plugin uses LangChain to generate AI answers with rich formatting.

Set LLM_MODEL_NAME, LLM_BASE_URL, LLM_API_KEY environment variables to
configure the LLM model. Bind python/searxng-addons/search_answers_llm/llm_answer.html
to your own template to customize the answer display.
"""
from __future__ import annotations
from os import environ
import traceback
import typing
import markdown

from searx.search.models import SearchQuery, EngineRef
from searx.result_types import EngineResults, Answer
from searx.plugins import Plugin, PluginInfo
from flask_babel import gettext
from searx.search import Search
from searx import engines
from pydantic import SecretStr

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langfuse.langchain import CallbackHandler as LangfuseLangchainCallbackHandler
from langfuse import get_client


if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg


try:
    langfuse = get_client()
    langchain_callback_handler = LangfuseLangchainCallbackHandler()
    print("Langfuse client initialized successfully.")
except Exception as exc:  # pragma: no cover - fallback when Langfuse is unavailable
    print("Langfuse client initialization failed: %s. Tracing disabled.", exc)

    class _DummySpan:  # type: ignore
        def update(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _DummyLangfuse:
        def start_as_current_span(self, *_, **__):
            return _DummySpan()

        def shutdown(self):
            pass

        def flush(self):
            pass

    class _DummyCallbackHandler:
        def __init__(self, *_, **__):
            pass

    langfuse = _DummyLangfuse()
    langchain_callback_handler = _DummyCallbackHandler()


class SXNGPlugin(Plugin):
    """LangChain LLM Answer Plugin that generates contextual answers with rich formatting."""

    id = "langchain_llm"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        print(f"[DEBUG] LangChain plugin initialized with active={plg_cfg.active}")

        self.info = PluginInfo(
            id=self.id,
            name=gettext("LangChain LLM"),
            description=gettext("Generate AI answers using LLM with rich formatting"),
            preference_section="general",
        )

        self.model_name = environ.get("LLM_MODEL_NAME", "gemini-2.0-flash")
        # Initialize ChatOpenAI once and reuse
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.7,
            base_url=environ.get(
                "LLM_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            api_key=SecretStr(environ.get("LLM_API_KEY", "dummy-key")),
        )

        # Initialize markdown converter with common extensions
        self.md_converter = markdown.Markdown(
            extensions=["extra", "codehilite", "toc"],
            extension_configs={"codehilite": {"css_class": "highlight"}},
        )

    def post_search(
        self, request: "SXNG_Request", search: "SearchWithPlugins"
    ) -> EngineResults:
        results = EngineResults()

        print(f"[DEBUG] post_search called for query: {search.search_query.query}")

        # Only process on first page
        if search.search_query.pageno > 1:
            print("[DEBUG] Skipping, not on first page.")
            return results

        query = search.search_query.query
        print(f"[DEBUG] Processing query: {query}")

        try:
            # Get search context from Google and DuckDuckGo
            search_context = self._get_search_context(query)

            if search_context:
                print(
                    f"[DEBUG] Retrieved {len(search_context)} search results for context"
                )

                # Generate LLM response with search context
                llm_answer_html = self._generate_contextual_answer_html(
                    query, search_context
                )

                if llm_answer_html:
                    print("[DEBUG] Generated contextual HTML answer")

                    # Create Answer with custom template
                    answer = Answer(
                        answer=llm_answer_html,
                        template="answer/llm_answer.html",  # Use our custom template
                    )
                    results.add(answer)
                    print("[DEBUG] Added HTML Answer to results")
                else:
                    print("[DEBUG] No contextual answer generated")
            else:
                print(
                    "[DEBUG] No search context retrieved, falling back to simple answer"
                )
                # Fallback to simple answer if no search context
                simple_answer_html = self._generate_simple_answer_html(query)
                if simple_answer_html:
                    answer = Answer(
                        answer=simple_answer_html, template="answer/llm_answer.html"
                    )
                    results.add(answer)

        except Exception as e:
            print(f"[DEBUG] Exception in post_search: {e}")

            traceback.print_exc()

        return results

    def _get_search_context(self, query: str) -> list[dict]:
        """Fetch search results from Google and DuckDuckGo for context."""
        print(f"[DEBUG] Fetching search context for: {query}")

        try:
            # Create engine references for Google and DuckDuckGo
            engine_refs = []

            # Check if Google is available and enabled
            if "google" in engines.engines:
                engine_refs.append(EngineRef("google", "general"))
                print("[DEBUG] Added Google engine")

            # Check if DuckDuckGo is available and enabled
            if "duckduckgo" in engines.engines:
                engine_refs.append(EngineRef("duckduckgo", "general"))
                print("[DEBUG] Added DuckDuckGo engine")

            if not engine_refs:
                print("[DEBUG] No suitable engines found")
                return []

            # Create a search query for just these engines
            context_search_query = SearchQuery(
                query=query,
                engineref_list=engine_refs,
                lang="en-US",
                safesearch=0,
                pageno=1,
                timeout_limit=5.0,  # 5 second timeout for context search
            )

            print(f"[DEBUG] Created SearchQuery with {len(engine_refs)} engines")

            # Execute the search
            context_search = Search(context_search_query)
            context_results = context_search.search()

            # Extract relevant results
            ordered_results = context_results.get_ordered_results()
            print(f"[DEBUG] Retrieved {len(ordered_results)} raw results")

            # Convert to simplified format for LLM context
            search_context = []
            for i, result in enumerate(ordered_results[:5]):  # Top 5 results
                try:
                    context_item = {
                        "title": getattr(result, "title", ""),
                        "content": getattr(result, "content", ""),
                        "url": getattr(result, "url", ""),
                        "engine": getattr(result, "engine", ""),
                    }

                    # Filter out empty results
                    if context_item["title"] or context_item["content"]:
                        search_context.append(context_item)
                        print(
                            f"[DEBUG] Added result {i+1}: {context_item['title'][:50]}..."
                        )

                except Exception as e:
                    print(f"[DEBUG] Error processing result {i}: {e}")
                    continue

            print(f"[DEBUG] Final search context: {len(search_context)} items")
            return search_context

        except Exception as e:
            print(f"[DEBUG] Error in _get_search_context: {e}")

            traceback.print_exc()
            return []

    def _generate_contextual_answer_html(
        self, query: str, search_context: list[dict]
    ) -> str:
        """Generate LLM answer with markdown formatting using search results as context."""
        print(f"[DEBUG] Generating contextual markdown answer for: {query}")

        try:
            # Use the pre-initialized ChatOpenAI instance
            llm = self.llm

            # Prepare context from search results
            context_text = self._format_search_context(search_context)

            # Create messages with search context - Updated to request markdown
            messages = [
                SystemMessage(
                    content="""You are a helpful Search Engine assistant that provides accurate answers and sources based on search results.
                    Identify the most important information and links from the search results.
                    Format your response using Markdown syntax for better readability.
                    Warn against potential malicious links when encounterd.
                    Keep the response concise but well-formatted in Markdown."""
                ),
                HumanMessage(
                    content=f"""Query: {query}

Search Results Context:
{context_text}

Based on the search results above, provide a helpful and accurate answer to the query using Markdown formatting. If the search results don't contain relevant information, say so and provide what general knowledge you can."""
                ),
            ]

            # Generate response
            response = llm.invoke(messages)
            answer = str(response.content).strip()
            langfuse.flush()

            print(f"[DEBUG] Generated contextual response: {answer[:100]}...")

            # Create formatted HTML answer from markdown
            formatted_answer = self._format_html_answer(answer, has_context=True)
            return formatted_answer

        except Exception as e:
            print(f"[DEBUG] Error in _generate_contextual_answer_html: {e}")

            traceback.print_exc()
            return ""

    def _generate_simple_answer_html(self, query: str) -> str:
        """Generate a simple LLM answer with markdown formatting (fallback)."""
        print(f"[DEBUG] Generating simple markdown answer for: {query}")

        try:
            # Use the pre-initialized ChatOpenAI instance
            llm = self.llm

            # Create simple messages - Updated to request markdown
            messages = [
                SystemMessage(
                    content="""You are a helpful assistant that provides concise answers using Markdown formatting.
                    Use Markdown syntax like **bold**, *italics*, bullet lists, and code blocks for better readability.
                    Keep responses brief but well-formatted."""
                ),
                HumanMessage(
                    content=f"Question: {query}\n\nProvide a brief, helpful answer using Markdown formatting:"
                ),
            ]

            # Generate response
            response = llm.invoke(messages)
            answer = str(response.content).strip()
            langfuse.flush()

            print(f"[DEBUG] Generated simple response: {answer[:100]}...")

            # Create formatted HTML answer from markdown
            formatted_answer = self._format_html_answer(answer, has_context=False)
            return formatted_answer

        except Exception as e:
            print(f"[DEBUG] Error in _generate_simple_answer_html: {e}")

            traceback.print_exc()
            return ""

    def _format_html_answer(self, markdown_answer: str, has_context: bool) -> str:
        """Convert markdown answer to HTML and add header/footer with model info."""
        try:
            # Convert markdown to HTML
            html_content = self.md_converter.convert(markdown_answer)

            # Reset the converter for next use
            self.md_converter.reset()

            context_badge = (
                "with search context" if has_context else "general knowledge"
            )
            model_name = self.model_name

            # GitHub repository URL - Replace with your actual repository
            github_repo_url = "https://github.com/bearlike/scripts"

            formatted_answer = f"""
            <div class="llm-header" style="margin-bottom: 12px;">
                <strong style="color: #007bff;">🤖 AI Assistant</strong>
                <span style="color: #6c757d; font-size: 0.9em;">({context_badge})</span>
            </div>
            <div class="llm-content" style="margin-bottom: 12px;">
                {html_content}
            </div>
            <div class="llm-footer" style="border-top: 1px solid #e9ecef; padding-top: 8px; margin-top: 12px; font-size: 0.85em; color: #6c757d; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="margin-right: 12px;">Model: <strong>{model_name}</strong></span>
                    <span>⚠️ AI responses may include mistakes.</span>
                </div>
                <div>
                    <a href="{github_repo_url}" target="_blank" style="text-decoration: none; display: inline-flex; align-items: center; background: #24292e; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">
                        <svg style="width: 16px; height: 16px; margin-right: 4px; fill: currentColor;" viewBox="0 0 24 24">
                            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                        </svg>
                        bearlike/scripts
                    </a>
                </div>
            </div>
            """

            return formatted_answer.strip()

        except Exception as e:
            print(f"[DEBUG] Error in _format_html_answer: {e}")

            traceback.print_exc()
            # Fallback to original text if markdown conversion fails
            return f"<div>{markdown_answer}</div>"

    def _format_search_context(self, search_context: list[dict]) -> str:
        """Format search results into text context for the LLM."""
        if not search_context:
            return "No search results available."

        context_parts = []
        for i, result in enumerate(search_context, 1):
            context_parts.append(f"Result {i}:")
            context_parts.append(f"Title: {result.get('title', 'N/A')}")

            content = result.get("content", "")
            if content:
                # Truncate content to avoid token limits
                content = content[:300] + "..." if len(content) > 300 else content
                context_parts.append(f"Content: {content}")

            source = result.get("engine", "Unknown")
            context_parts.append(f"Source: {source}")
            context_parts.append("")  # Empty line between results

        return "\n".join(context_parts)
