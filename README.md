# LangGraph Serving with BentoML

This repo demonstrates how to serve LangGraph agent application with BentoML.

## Overview


- **AI Agent Serving**: Serving LangGraph Agent as REST API for easy integration
- **Flexible Invocation**: Supports both synchronous and asynchronous (queue-based) interactions.
- **Deployment Options**: Run locally or deploy to BentoCloud for scalability.
- **LLM Deployment**: Use external LLM APIs or deploy open-source LLM together with the Agent API service

This project serves as a reference implementation designed to be hackable, providing a  foundation for building and customizing your own AI agent solutions. 


## Getting Started

Download source code:
```bash
git clone https://github.com/bentoml/BentoLangGraph.git
cd BentoLangGraph/
```

Follow the step-by-step guide for serving & deploying LangGraph agents with BentoML:

- [Anthropic Claude 3.5 Sonnet](langgraph-anthropic/)
- [Mistral 7B Instruct](langgraph-mistral/)


## Troubleshoot

When running the example code which uses DuckDuckGo search tool, you may run into the 
following rate limit error:
```
RatelimitException('https://duckduckgo.com/ 202 Ratelimit')
```

You may use a different tool from LangChain's pre-built tools list [here](https://python.langchain.com/v0.2/docs/integrations/tools/) or create a [custom tool](https://python.langchain.com/v0.2/docs/how_to/custom_tools/).

For example, you can use exa to replace DuckDuckGo for search:
```diff
- from langchain_community.tools import DuckDuckGoSearchRun
- tools = [search]
+ from exa_search import retrieve_web_content
+ tools = [retrieve_web_content]
```

Interested in using LangGraph with other open-source LLMs? Checkout [BentoVLLM](https://github.com/bentoml/BentoVLLM) for more sample code.


## Community

Join the [BentoML developer community](https://l.bentoml.com/join-slack) on Slack for more support and discussions!