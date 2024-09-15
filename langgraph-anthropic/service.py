import bentoml
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from workflow import workflow

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
class LangGraphService:
    def __init__(self):
        # Initialize memory to persist state between graph runs
        checkpointer = MemorySaver()

        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable.
        self.app = workflow.compile(checkpointer=checkpointer)

    @bentoml.task
    def invoke(
        self, 
        input_query: str="what is the weather in sf",
    ) -> str:
        final_state = self.app.invoke(
            {"messages": [HumanMessage(content="what is the weather in sf")]},
            config={"configurable": {"thread_id": 42}}
        )
        return final_state["messages"][-1].content