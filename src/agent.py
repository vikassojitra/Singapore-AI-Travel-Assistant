import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import GOOGLE_API_KEY, LLM_MODEL
from rag import singapore_knowledge_search
from prompt import get_travel_prompt

async def build_agent_executor():
    client = MultiServerMCPClient({
        "currency_service": {
            "command": sys.executable,
            "args": ["mcp_currency.py"],
            "transport": "stdio"
        },
        "weather_service": {
            "command": sys.executable,
            "args": ["mcp_weather.py"],
            "transport": "stdio"
        }
    })
    mcp_tools = await client.get_tools()
    tools = [singapore_knowledge_search] + mcp_tools
    
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.2, google_api_key=GOOGLE_API_KEY)
    prompt = get_travel_prompt()
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)