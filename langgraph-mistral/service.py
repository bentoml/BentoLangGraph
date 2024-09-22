from typing import Annotated, Literal, TypedDict, Any, List, Optional, Sequence
import json
import random
import string

import bentoml

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatResult
from langchain_core.tools import BaseTool
from pydantic import Field
from openai import OpenAIError

from mistral import MistralService

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

# Define the function that determines whether to continue or not
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


# Entry service defined in bentofile.yaml
@bentoml.service(
    workers=2,
    resources={
        "cpu": "2000m"
    },
    traffic={
        "concurrency": 16,
        "external_queue": True
    }
)
class SearchAgentService:
    # OpenAI compatible API
    llm_service = bentoml.depends(MistralService)

    def __init__(self):
        tools = [search]
        tool_node = ToolNode(tools)

        openai_api_base = f"{self.llm_service.client_url}/v1"
        self.model = ChatOpenAI(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            openai_api_key="N/A",
            openai_api_base=openai_api_base,
            temperature=0,
            verbose=True,
            http_client=self.llm_service.to_sync.client,
        ).bind_tools(tools)

        def call_model(state: MessagesState):
            messages = state['messages']
            response = self.model.invoke(messages)
            if isinstance(response, AIMessage):
                if response.tool_calls:
                    # Replace the tool_call id with a valid one for Mistral/Mixtral models
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

        self.app = workflow.compile()

    @bentoml.task
    async def invoke(
        self, 
        input_query: str="What is the weather in San Francisco today?",
    ) -> str:
        try:
            final_state = await self.app.ainvoke(
                {"messages": [HumanMessage(content=input_query)]}
            )
            return final_state["messages"][-1].content
        except OpenAIError as e:
            print(f"An error occurred: {e}")
            import traceback
            print(traceback.format_exc())
            return "I'm sorry, but I encountered an error while processing your request. Please try again later."