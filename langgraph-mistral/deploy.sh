#!/bin/bash

# Check if the 'huggingface' secret already exists
if ! bentoml secret list | awk '{print $1}' | grep -q "^huggingface$"; then
    # Check if the API key is provided as a command-line argument
    if [ $# -eq 1 ]; then
        HF_TOKEN=$1
    else
    # If not provided as an argument, check if it's set as an environment variable
        if [ -z "$HF_TOKEN" ]; then
            echo "Error: HF_TOKEN is not set. Please provide it as an argument or set it as an environment variable."
            exit 1
        fi
    fi
    echo "Creating 'huggingface' secret..."
    bentoml secret create huggingface HF_TOKEN=$HF_TOKEN
else
    echo "'huggingface' secret already exists. Skipping creation."
fi

bentoml deploy . --secret huggingface