# SearXNG Custom Search Engines

A collection of custom search engine integrations for [SearXNG](https://github.com/searxng/searxng), the privacy-respecting metasearch engine.

## Overview

This repository contains custom engine implementations that extend SearXNG's capabilities by integrating with various services and APIs. Each engine is designed to work seamlessly with SearXNG's architecture while providing specialized search functionality.

## 🔍 Available Engines

### 1. AI Search Assist (`search_answers_llm\plugins_langchain_llm.py`)

This SearXNG plugin generates contextual, AI-powered answers by hooking into the `post_search` process. It programmatically executes a secondary, targeted search against Google and DuckDuckGo using `SearchQuery` and `EngineRef` to gather real-time context for the user's query. This context is then sent to a LLM. The plugin injects this response as a custom `Answer` result type, overriding the default template to use a custom one with the `|safe` filter, ensuring the rich text is rendered correctly on the results page.

![SearXNG LLM Assist](/docs/search_llm_assist.png)

### 2. Homepage Dashboard Integration (`dashboard_services.py`)

Integrates with [`gethomepage/homepage`](https://github.com/gethomepage/homepage), a customizable home or startpage with Docker and service API support. This enables your home lab dashboard to become fully searchable using SearXNG.

**Motivation** - Managing many self-hosted services in my home lab was inconvenient. I needed to remember where each app lived and to search through my dashboard manually. With this integration, I can use homepage's API and add search and filtering so it's much easier to discover and launch any internal service directly from SearXNG.

**Features:**

- Case-insensitive substring matching works across service names, descriptions, and metadata
- Results are scored by relevance, with service name matches considered most important
- Supports hierarchical search through service groups and categories
- Displays service descriptions, server information, and container details in results
- Provides direct links to your self-hosted applications

![SearXNG Homepage Integration](/docs/searxng-homepage.png)
