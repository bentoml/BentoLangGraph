from __future__ import annotations

import typing, logging, traceback

import bentoml

from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IMAGE = bentoml.images.PythonImage(
    python_version="3.11", lock_python_packages=False, python_requirements="requirements.txt"
)


@tool
def search(query: str):
    """A wrapper around DuckDuckGo Search.
    Useful for when you need to answer questions about current events, current weather, latest news, up-to-date information, etc.
    Input should be a search query.
    """
    duckduckgo_search = DuckDuckGoSearchRun()

    res = duckduckgo_search.invoke({"query": query})
    return [res]


# Define the function that determines whether to continue or not
def should_continue(state: MessagesState) -> typing.Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return END


@bentoml.service(
    name="langgraph-anthropic-search-agent",
    workers=2,
    resources={"cpu": "2000m"},
    envs=[{"name": "ANTHROPIC_API_KEY"}],
    traffic={"concurrency": 16, "external_queue": True},
    labels={"owner": "bentoml-team", "project": "langgraph-anthropic"},
    image=IMAGE,
)
class SearchAgentService:
    @bentoml.on_startup
    def initialize_app(self):
        tools = [search]
        tool_node = ToolNode(tools)

        model = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0).bind_tools(tools)

        # Define the function that calls the model
        def call_model(state: MessagesState):
            messages = state["messages"]
            response = model.invoke(messages)
            # We return a list, because this will get added to the existing list
            return {"messages": [response]}

        # Define a new graph
        workflow = StateGraph(MessagesState)

        # Define the two nodes we will cycle between
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)

        # Set the entrypoint as `agent`
        # This means that this node is the first one called
        workflow.add_edge(START, "agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            should_continue,
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")
        self.app = workflow.compile()

    @bentoml.task
    async def invoke(
        self,
        input_query: str = "What is the weather in San Francisco today?",
    ) -> str:
        try:
            final_state = await self.app.ainvoke({"messages": [HumanMessage(content=input_query)]})
            return final_state["messages"][-1].content
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            logger.error(traceback.format_exc())
            return "I'm sorry, but I encountered an error while processing your request. Please try again later."

    @bentoml.api
    async def stream(
        self,
        input_query: str = "What is the weather in San Francisco today?",
    ) -> typing.AsyncGenerator[str, None]:
        async for event in self.app.astream_events({"messages": [HumanMessage(content=input_query)]}, version="v2"):
            yield str(event) + "\n"
