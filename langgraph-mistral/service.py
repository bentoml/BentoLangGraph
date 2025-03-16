from __future__ import annotations

import logging, typing, random, string, traceback

import bentoml, fastapi

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, AIMessage
from openai import OpenAIError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ENGINE_CONFIG = {
    "model": "mistralai/Ministral-8B-Instruct-2410",
    "tokenizer_mode": "mistral",
    "max_model_len": 4096,
    "enable_prefix_caching": False,
}
IMAGE = (
    bentoml.images.PythonImage(python_version="3.11", lock_python_packages=False)
    .requirements_file("requirements.txt")
    .run("uv pip install flashinfer-python --find-links https://flashinfer.ai/whl/cu124/torch2.5")
)
openai_api_app = fastapi.FastAPI()


@bentoml.asgi_app(openai_api_app, path="/v1")
@bentoml.service(
    name="bentovllm-ministral-8b-instruct-2410-service",
    traffic={"concurrency": 128, "timeout": 300},
    resources={"gpu": 1, "gpu_type": "nvidia-l4"},
    envs=[
        {"name": "HF_TOKEN"},
        {"name": "UV_NO_PROGRESS", "value": 1},
        {"name": "HF_HUB_DISABLE_PROGRESS_BARS", "value": 1},
        {"name": "VLLM_ATTENTION_BACKEND", "value": "FLASH_ATTN"},
    ],
    labels={"owner": "bentoml-team", "type": "prebuilt"},
    image=IMAGE,
)
class LLM:
    model_id = ENGINE_CONFIG["model"]
    model = bentoml.models.HuggingFaceModel(model_id, exclude=["consolidated*", "*.pth", "*.pt"])

    def __init__(self):
        from openai import AsyncOpenAI

        self.openai = AsyncOpenAI(base_url="http://127.0.0.1:3000/v1", api_key="dummy")

    @bentoml.on_startup
    async def init_engine(self) -> None:
        import vllm.entrypoints.openai.api_server as vllm_api_server

        from vllm.utils import FlexibleArgumentParser
        from vllm.entrypoints.openai.cli_args import make_arg_parser

        args = make_arg_parser(FlexibleArgumentParser()).parse_args([])
        args.model = self.model
        args.disable_log_requests = True
        args.max_log_len = 1000
        args.served_model_name = [self.model_id]
        args.request_logger = None
        args.disable_log_stats = True
        for key, value in ENGINE_CONFIG.items():
            setattr(args, key, value)

        router = fastapi.APIRouter(lifespan=vllm_api_server.lifespan)
        OPENAI_ENDPOINTS = [
            ["/chat/completions", vllm_api_server.create_chat_completion, ["POST"]],
            ["/models", vllm_api_server.show_available_models, ["GET"]],
        ]

        for route, endpoint, methods in OPENAI_ENDPOINTS:
            router.add_api_route(path=route, endpoint=endpoint, methods=methods, include_in_schema=True)
        openai_api_app.include_router(router)

        self.engine_context = vllm_api_server.build_async_engine_client(args)
        self.engine = await self.engine_context.__aenter__()
        self.model_config = await self.engine.get_model_config()
        self.tokenizer = await self.engine.get_tokenizer()
        args.tool_call_parser = "mistral"
        args.enable_auto_tool_choice = True

        await vllm_api_server.init_app_state(self.engine, self.model_config, openai_api_app.state, args)

    @bentoml.on_shutdown
    async def teardown_engine(self):
        await self.engine_context.__aexit__(GeneratorExit, None, None)


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
    if last_message.tool_calls:
        return "tools"
    return END


def generate_valid_tool_call_id():
    """Generate a valid 9-character tool_call_id for Mistral/Mixtral models.
    Context:
    Some model architectures, notably Mistral/Mixtral, also require a tool_call_id here, which should be 9 randomly-generated alphanumeric characters, and assigned to the id key of the tool call dictionary. The same key should also be assigned to the tool_call_id key of the tool response dictionary below, so that tool calls can be matched to tool responses. So, for Mistral/Mixtral models, the code above would be:

    https://huggingface.co/docs/transformers/main/chat_templating#advanced-tool-use--function-calling
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=9))


@bentoml.service(
    name="langgraph-mistral-search-agent",
    workers=2,
    resources={"cpu": "2000m"},
    traffic={"concurrency": 16, "external_queue": True},
    labels={"owner": "bentoml-team", "project": "langgraph-mistral"},
    image=IMAGE,
)
class SearchAgentService:
    # OpenAI compatible API
    llm_service = bentoml.depends(LLM)

    def __init__(self):
        tools = [search]
        self.tools = ToolNode(tools)
        self.model = ChatOpenAI(
            model=LLM.inner.model_id,
            openai_api_key="N/A",
            openai_api_base=f"{self.llm_service.client_url}/v1",
            temperature=0,
            verbose=True,
            http_client=self.llm_service.to_sync.client,
        ).bind_tools(tools)

    @bentoml.on_startup
    def initialize_app(self):
        def call_model(state: MessagesState):
            messages = state["messages"]
            response = self.model.invoke(messages)
            if isinstance(response, AIMessage):
                if response.tool_calls:
                    # Replace the tool_call id with a valid one for Mistral/Mixtral models
                    for tool_call in response.tool_calls:
                        original_id = tool_call["id"]
                        tool_call["id"] = generate_valid_tool_call_id()
                        for tc in response.additional_kwargs["tool_calls"]:
                            if tc["id"] == original_id:
                                tc["id"] = tool_call["id"]
            return {"messages": [response]}

        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", self.tools)
        workflow.add_edge(START, "agent")

        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")

        self.app = workflow.compile()

    @bentoml.api
    async def stream(
        self,
        input_query: str = "What is the weather in San Francisco today?",
    ) -> typing.AsyncGenerator[str, None]:
        async for event in self.app.astream_events({"messages": [HumanMessage(content=input_query)]}, version="v2"):
            yield str(event) + "\n"

    @bentoml.task
    async def invoke(
        self,
        input_query: str = "What is the weather in San Francisco today?",
    ) -> str:
        try:
            final_state = await self.app.ainvoke({"messages": [HumanMessage(content=input_query)]})
            return final_state["messages"][-1].content
        except OpenAIError as e:
            logger.error(f"An error occurred: {e}")
            logger.error(traceback.format_exc())
            return "I'm sorry, but I encountered an error while processing your request. Please try again later."
