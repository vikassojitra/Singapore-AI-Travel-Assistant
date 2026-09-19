import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from agent import build_agent_executor

agent_executor = None

async def chat_function(message, history):
    global agent_executor
    if agent_executor is None:
        agent_executor = await build_agent_executor()
    
    # Convert Gradio chat history (both dict and tuple formats) to LangChain messages
    chat_history = []
    for turn in history:
        # Case A: Gradio dict format ({'role': 'user'|'assistant', 'content': '...'})
        if isinstance(turn, dict):
            role = turn.get("role")
            content = turn.get("content", "")
            if role == "user" and content:
                chat_history.append(HumanMessage(content=str(content)))
            elif role == "assistant" and content:
                chat_history.append(AIMessage(content=str(content)))
        
        # Case B: Gradio tuple/list format ([user_msg, bot_msg])
        elif isinstance(turn, (list, tuple)) and len(turn) >= 2:
            user_msg, bot_msg = turn[0], turn[1]
            if user_msg:
                chat_history.append(HumanMessage(content=str(user_msg)))
            if bot_msg:
                chat_history.append(AIMessage(content=str(bot_msg)))
            
    response = await agent_executor.ainvoke({
        "input": message,
        "chat_history": chat_history
    })
    return response["output"]

demo = gr.ChatInterface(
    fn=chat_function,
    title="AI Travel Planning Assistant (Singapore)",
    description="Ask about attractions, culture, weather forecasts, currency conversions, or weather-adjusted itineraries."
)

if __name__ == "__main__":
    demo.launch()