import argparse
import bentoml

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for LangGraph Service")
    parser.add_argument("--url", default="http://localhost:3000", help="Deployed URL of the service")
    parser.add_argument(
        "--query", default="What's the weather in San Francisco today?", help="Query to send to the service"
    )
    args = parser.parse_args()

    client = bentoml.SyncHTTPClient(args.url)
    print(client.invoke(args.query))
