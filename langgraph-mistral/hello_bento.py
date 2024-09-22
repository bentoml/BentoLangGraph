from openai import OpenAI

# openai_api_base = "https://bentovllm-llama-3-1-8-b-instruct-service-slgm-d3767914.mt-guc1.bentoml.ai/v1"
openai_api_base = "http://209.51.170.115:3000/v1"


client = OpenAI(base_url=openai_api_base)
# openai_api_base = "https://bentovllm-llama-3-1-8-b-instruct-service-slgm-d3767914.mt-guc1.bentoml.ai/v1"


# TOOLS_TEMPLATE = {
#     # Keywords used by the model to call functions. Must be defined to catch function calls:
#     "call_token_start":
#     "<tool_call>",
#     "call_token_end":
#     "</tool_call>",

#     # Keywords used to define functions. Used to present the list of functions to the llm
#     "tool_token_start":
#     "<tool>",
#     "tool_token_end":
#     "</tool>",

#     # Response keywords. Used to present the values returned by the functions
#     "response_token_start":
#     "<tool_response>",
#     "response_token_end":
#     "</tool_response>",

#     # Call notifications to the model (optional)
#     "tool_call_notif_noarg_start":
#     "",  #
#     "tool_call_notif_noarg_end":
#     "was called with no argument",
#     "tool_call_notif_args_start":
#     "",
#     "tool_call_notif_args_end":
#     "was called with arguments",

#     # Instructions (guided generation if tool_choice is defined on a specific function)
#     "function_guided":
#     "You must call the following function at least one time to answer the question. You may call it multiple times if needed:",

#     # Instructions (auto mode, if tool_choice equals "auto" or None)
#     "function_list_start":
#     "The following is a list of external functions that may be called to complete certain tasks:",
#     "function_list_end":
#     """End of list
# * Whenever the user asks you something, you can either respond directly or invoke a function if it is present in the previous list.
# * The decision to invoke a function is yours, only invoke a function if it is necessary to answer the user's question
# * If you need to call at least one function, your message should contain only a list of function calls and nothing else; the function calls are the response.""",

#     # Instructions on how to call functions. Must follow call_token_start and call_token_end to get the parser work
#     "function_call_instruct":
#     """For each function call return a valid json object (using quotes) with function name and arguments within <tool_call>{ }</tool_call> XML tags as follows::
# * With arguments:
# <tool_call>{ "name": "function_name", "arguments": {"argument_name": "value"} }</tool_call>
# * Without arguments:
# <tool_call>{ "name": "function_name", "arguments": null }</tool_call>
# End of functions instructions"""
# }

# EXTRA_BODY_OPENAI = {"stop_token_ids": [32000], "tool_params": TOOLS_TEMPLATE}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_delivery_date",
            "description": "Get the delivery date for a customer's order. Call this whenever you need to know the delivery date, for example when a customer asks 'Where is my package'",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The customer's order ID.",
                    },
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        }
    }
]


messages = [
    {"role": "system", "content": "You are a helpful customer support assistant. Use the supplied tools to assist the user."},
    {"role": "user", "content": "Hi, can you tell me the delivery date for my order with id DA1948237?"}
]

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    # model="mistralai/Mistral-7B-v0.3",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    # extra_body=EXTRA_BODY_OPENAI
)
print(response)