import bentoml

if __name__ == "__main__":
    client = bentoml.SyncHTTPClient("http://localhost:3000")
    response = client.invoke("What's the weather in San Francisco?")
    print(response)