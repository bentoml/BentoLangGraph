## Run locally
1. pip install -r requirements.txt
2. export ANTHROPIC_API_KEY=<your-api-key>
3. bentoml serve .
4. python client.py

## Deploy to BentoCloud

1. bentoml cloud login
2. ./deploy.sh <your-anthropic-api-key>
