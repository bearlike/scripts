# SearXNG Custom Search Engines

A collection of custom search engine integrations for [SearXNG](https://github.com/searxng/searxng), the privacy-respecting metasearch engine.

## Overview

This repository contains custom engine implementations that extend SearXNG's capabilities by integrating with various services and APIs. Each engine is designed to work seamlessly with SearXNG's architecture while providing specialized search functionality.

## 🔍 Available Engines

### 1. Homepage Dashboard Integration (`dashboard_services.py`)

Integrates with [`gethomepage/homepage`](https://github.com/gethomepage/homepage) to search through your self-hosted services and applications.

**Features:**

- Search across all configured services in your homepage dashboard
- Hierarchical search through service groups and categories
- Rich results showing service descriptions, server info, and container details
- Direct links to your self-hosted applications

![SearXNG Homepage Integration](/docs/searxng-homepage.png)
