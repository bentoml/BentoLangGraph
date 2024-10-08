import bentoml
from langchain_core.messages import HumanMessage
from typing import AsyncGenerator

from agent import workflow

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
    def __init__(self):
        self.app = workflow.compile()

    @bentoml.task
    async def invoke(
        self, 
        input_query: str="What is the weather in San Francisco today?",
    ) -> str:
        final_state = await self.app.ainvoke(
            {"messages": [HumanMessage(content=input_query)]}
        )
        return final_state["messages"][-1].content

    @bentoml.api
    async def stream(
        self,
        input_query: str="What is the weather in San Francisco today?",
    ) -> AsyncGenerator[str, None]:
        async for event in self.app.astream_events(
            {"messages": [HumanMessage(content=input_query)]},
            version="v2"
        ):
            yield str(event) + "\n"
