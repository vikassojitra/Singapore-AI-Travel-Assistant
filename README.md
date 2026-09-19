# AI Travel Planning Assistant

A Singapore-focused travel planning assistant that combines retrieval-augmented generation (RAG), tool calling, and real-time external services to answer destination, itinerary, weather, and currency questions.

## Overview

This project is designed for a narrow and reliable travel domain:

- It answers questions only about Singapore.
- It uses a local FAISS vector knowledge base for destination facts and recommendations.
- It calls MCP tools for current weather forecasts and currency conversion.
- It keeps context across chat turns to support multi-step travel planning.

The application is built with:

- Python
- Gradio for the chat UI
- LangChain + LangChain Google GenAI
- FAISS for vector search
- MCP (Model Context Protocol) servers for weather and currency tools

---

## Architecture

### 1. Frontend / chat layer

File: `src/app.py`

- Launches the Gradio chat interface.
- Converts Gradio message history into LangChain message objects.
- Calls the agent executor with the current user request and prior conversation.
- Returns the assistant's output back to the UI.

### 2. Agent orchestration

File: `src/agent.py`

This module builds the agent executor that coordinates:

- the Singapore RAG tool
- weather MCP tool server
- currency MCP tool server
- the Gemini LLM

Flow:

1. Starts MCP servers using `MultiServerMCPClient`.
2. Gets tools exposed by the MCP servers.
3. Combines them with the Singapore knowledge search tool.
4. Creates a tool-calling agent with a system prompt.
5. Returns an `AgentExecutor` to handle reasoning and tool invocation.

### 3. Prompt and behavior rules

File: `src/prompt.py`

The system prompt enforces several critical rules:

- The assistant is specialized only in Singapore.
- It must refuse non-Singapore destinations.
- It should use the RAG tool for destination facts and recommendations.
- It must use MCP tools for weather and currency data.
- It should preserve chat continuity across turns.
- It should combine weather + itinerary logic when needed.
- It must distinguish between knowledge-base facts, tool data, and LLM suggestions.

### 4. Knowledge retrieval (RAG)

File: `src/rag.py`

This module loads the local FAISS index and exposes a LangChain tool:

- `singapore_knowledge_search(query: str) -> str`

Behavior:

- Embeds the search query using the configured Google embedding model.
- Looks up the top relevant chunks in FAISS.
- Returns each result with content plus metadata: source title and source URL.

### 5. Ingestion pipeline

File: `src/ingest.py`

This script creates the knowledge base from public Singapore travel sources.

It does the following:

- Fetches web pages from a curated list of Singapore travel sources.
- Cleans page content by removing navigation and UI noise.
- Splits the content into semantic chunks.
- Uses Google embeddings to create vector representations.
- Stores them in a local FAISS database under `src/faiss_index/`.

### 6. MCP tools

Files:

- `src/mcp_weather.py`
- `src/mcp_currency.py`

These are FastMCP servers launched as subprocesses via stdio transport.

#### Weather service

The weather MCP server exposes:

- `get_current_weather(city: str = "Singapore")`
- `get_forecast(city: str = "Singapore", days: int = 3)`

It uses Open-Meteo geocoding + forecasting APIs to fetch current weather and multi-day forecasts.

#### Currency service

The currency MCP server exposes:

- `convert_currency(amount: float, from_currency: str, to_currency: str)`

It fetches exchange-rate data from Frankfurter.

---

## Knowledge Base Sources

The knowledge base is built from the following Singapore-focused sources:

| Source | URL |
| --- | --- |
| Wikivoyage: Singapore Travel Guide | https://en.wikivoyage.org/wiki/Singapore |
| Visit Singapore: Essential Travel Information | https://www.visitsingapore.com/travel-tips/essential-travel-information/ |
| Visit Singapore: Sample Itineraries | https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/ |
| Visit Singapore: Things to Do | https://www.visitsingapore.com/things-to-do/top-things-to-do/ |
| Visit Singapore: Singapore Tours | https://www.visitsingapore.com/things-to-do/singapore-tours/ |

These are intentionally curated to support Singapore attractions, culture, transit, food, and itinerary guidance.

---

## RAG Workflow

The RAG workflow is intentionally simple and explicit:

1. User asks a travel question in the UI.
2. The Gradio app turns the conversation into LangChain messages.
3. The agent receives the message and decides whether tools are needed.
4. For destination knowledge, the agent uses `singapore_knowledge_search`.
5. The query is embedded and matched against the FAISS vector store.
6. The top retrieved chunks are returned with metadata, including the source title and URL.
7. The LLM uses those chunks as grounded context before generating a response.

This is designed to keep responses informative, source-aware, and scoped to Singapore.

---

## MCP Tool Strategy

The project distinguishes between two kinds of answers:

- Knowledge-base answers: factual Singapore travel information from the local vector store.
- Real-time answers: weather and exchange rates from external tools.

This separation matters because:

- RAG answers are grounded in the curated knowledge base.
- MCP tool outputs represent live data.
- The system prompt explicitly tells the model to cite the source or clearly state when it is using a tool.

Example patterns:

- “Based on the Singapore knowledge base...”
- “According to the current forecast tool...”
- “Using the currency conversion tool...”

---

## Prompt and Context Strategy

The prompt in `src/prompt.py` uses a strict system prompt to steer the model.

### Core strategies

- Destination scope enforcement: only Singapore is allowed.
- Cite sources: knowledge-base claims should include title and URL.
- Tool usage discipline: weather and currency data must come from MCP tools, not guessed.
- Multi-turn continuity: user preferences and previous suggestions persist across conversation turns.
- Weather-adjusted planning: forecast data can trigger indoor/outdoor itinerary replacement.
- Explicit uncertainty handling: if information is missing, say no instead of inventing details.

### Context management

The agent passes:

- the current user input
- prior chat history (`chat_history`)
- scratchpad state used by the tool-calling agent

This allows the assistant to retain details such as:

- budget range
- travel dates
- group type
- preferred neighborhoods
- indoor vs outdoor preferences
- earlier itinerary recommendations

---

## Configuration and Environment

The project uses environment variables from a `.env` file in the project root.

File: `src/config.py`

Expected variables:

```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL_NAME=gemini-1.5-flash
EMBEDDING_MODEL=models/embedding-001
```

Notes:

- `GOOGLE_API_KEY` is required for Gemini and embeddings.
- `GOOGLE_MODEL_NAME` sets the ChatGoogleGenerativeAI model.
- `EMBEDDING_MODEL` is used for FAISS indexing and retrieval.

---

## Setup Instructions

### 1. Create a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

At the project root, create a file named `.env` with the required values:

```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL_NAME=gemini-1.5-flash
EMBEDDING_MODEL=models/embedding-001
```

### 4. Build the FAISS knowledge base

If the index is missing or needs refresh:

```bash
python src/ingest.py
```

This script scrapes the source pages, builds chunks, embeds them, and saves the FAISS index locally.

### 5. Run the app

```bash
python src/app.py
```

Then open the local Gradio URL shown in the terminal.

---

## Project Files

```text
AI_Travel_Planning_Assistant/
├── requirements.txt
├── .env
├── Sample Q&A
├── src/
│   ├── app.py
│   ├── agent.py
│   ├── config.py
│   ├── ingest.py
│   ├── mcp_currency.py
│   ├── mcp_weather.py
│   ├── prompt.py
│   ├── rag.py
│   └── faiss_index/
│       └── index.faiss
```

---

## How the System Behaves in Practice (Sample Q&A)

Example user interactions:

- “Plan a 2-day Singapore itinerary for a family with kids.”
- “Check the weather this weekend and adjust my outdoor plan.”
- “Convert 10,000 INR to SGD for my trip budget.”
- “What are the best food neighborhoods in Singapore?”

The assistant will:

- use RAG for Singapore-specific factual guidance
- use weather MCP tools for live conditions
- use currency MCP tool for exchange rates
- maintain the conversation context across turns
- refuse anything outside the Singapore scope

#### Note: For Live example, kindly refer files inside **Sample Q&A** folder.

---

## Notes and Limitations

- The assistant is intentionally restricted to Singapore; non-Singapore questions are out of scope.
- The FAISS database is only as current as the ingestion run.
- The knowledge base is based on a curated set of websites and is not a full general travel database.
- Weather and currency responses depend on external APIs being available.

This design keeps the assistant trustworthy, focused, and grounded in a specific destination domain.

## Author

- Vikas Sojitra

## Video Demonstration

- **Google Drive Link:** https://drive.google.com/file/d/1tWFhKOeK3nFoDIDr7Vua5K6iVZNbj8iy/view?usp=sharing
