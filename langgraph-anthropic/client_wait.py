import time
import bentoml

if __name__ == "__main__":
    client = bentoml.SyncHTTPClient("http://localhost:3000")
    task = client.invoke.submit("What's the weather in San Francisco?")
    while task.get_status().value == "in_progress":
        print("Waiting for task to complete...")
        time.sleep(5)

    if task.get_status().value == "success":
        print("Result: ", task.get())
    else:
        print("Task failed")