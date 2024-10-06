from typing import Literal

import random
import string

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

duckduckgo_search = DuckDuckGoSearchRun()

@tool
def search(query: str):
    """A wrapper around DuckDuckGo Search.
    Useful for when you need to answer questions about current events, current weather, latest news, up-to-date information, etc. 
    Input should be a search query.
    """
    res = duckduckgo_search.invoke({"query": query})
    return [res]

tools = [search]
tool_node = ToolNode(tools)

# Standalone LLM deployed on BentoCloud for dev & debugging
openai_api_base = "https://bentovllm-mistral-7-b-instruct-v-03-service-cwc7-d3767914.mt-guc1.bentoml.ai/v1"

model = ChatOpenAI(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    openai_api_key="N/A",
    openai_api_base=openai_api_base,
    temperature=0,
    verbose=True,
).bind_tools(tools)

def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

def generate_valid_tool_call_id():
    """Generate a valid 9-character tool_call_id for Mistral/Mixtral models.
    Context:
    Some model architectures, notably Mistral/Mixtral, also require a tool_call_id here, which should be 9 randomly-generated alphanumeric characters, and assigned to the id key of the tool call dictionary. The same key should also be assigned to the tool_call_id key of the tool response dictionary below, so that tool calls can be matched to tool responses. So, for Mistral/Mixtral models, the code above would be:

    https://huggingface.co/docs/transformers/main/chat_templating#advanced-tool-use--function-calling
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=9))

def call_model(state: MessagesState):
    messages = state['messages']
    response = model.invoke(messages)
    if isinstance(response, AIMessage):
        if response.tool_calls:
            for tool_call in response.tool_calls:
                original_id = tool_call["id"]
                tool_call["id"] = generate_valid_tool_call_id()
                for tc in response.additional_kwargs['tool_calls']:
                    if tc['id'] == original_id:
                        tc['id'] = tool_call["id"]
    
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
)
workflow.add_edge("tools", 'agent')


if __name__ == "__main__":
    app = workflow.compile()
    final_state = app.invoke({"messages": [HumanMessage(content="what is the weather in sf today?")]})
    print(final_state["messages"][-1].content)
