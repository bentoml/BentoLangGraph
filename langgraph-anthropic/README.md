# Serving LangGraph app with BentoML

## Install dependencies
```bash
pip install -r requirements.txt
```

## Run locally

Set Anthropic API Key:
```bash
export ANTHROPIC_API_KEY=<your-api-key>
```

Spin up the REST API server:
```bash
bentoml serve .
```

## Invoke the endpoint

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
bentoml cloud login
```

Deploy:

```bash
./deploy.sh <your-anthropic-api-key>
```