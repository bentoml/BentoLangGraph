# LangGraph Agent with Mistral 7B

This project implements a LangGraph agent powered by the Mistral 7B language model. 

## Overview

- **AI Agent**: Utilizes LangGraph and Mistral 7B to build an AI agent that can search the web.
- **API**: Provides a REST API for easy integration.
- **Flexible Invocation**: Supports both synchronous and asynchronous (queue-based) interactions.
- **Deployment Options**: Run locally or deploy to BentoCloud for scalability.


## Run locally

Install dependencies
```bash
pip install -r requirements.txt
```

Set HuggingFace API Key for downloading the model:
```bash
export HF_TOEKN=<your-api-key>
```

Spin up the REST API server:
```bash
bentoml serve .
```

Invoke the endpoint

Syncrounous client:
```bash
python client.py --url http://localhost:3000/ --query "What's the weather in the Bay Area?"
```

Invoke via Async Queue:
```bash
python client_queue.py --url http://localhost:3000/ --query "What's the weather in the Bay Area?"
```

## Deploy to BentoCloud

Login to BentoCloud:
```bash
pip install bentoml
bentoml cloud login
```

Create secret:
```bash
bentoml secret create huggingface HF_TOKEN=$HF_TOKEN
```

Deploy:

```bash
bentoml deploy . --name search-agent --secret huggingface
```

Invoke the endpoint:
```bash
DEPLOYED_ENDPOINT=$(bentoml deployment get search-agent -o json | jq -r ".endpoint_urls[0]")

python client.py --query "What's the weather in San Francisco today?" --url $DEPLOYED_ENDPOINT
```