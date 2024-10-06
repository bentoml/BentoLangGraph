import argparse

import bentoml

parser = argparse.ArgumentParser(description="Client for LangGraph Service")
parser.add_argument("--url", default="http://localhost:3000", help="Deployed URL of the service")
parser.add_argument("--query", default="What's the weather in San Francisco today?", help="Query to send to the service")
args = parser.parse_args()

if __name__ == "__main__":
    client = bentoml.SyncHTTPClient(args.url)
    response = client.invoke(args.query)
    print(response)