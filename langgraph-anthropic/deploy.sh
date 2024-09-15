#!/bin/bash

# Check if the API key is provided as a command-line argument
if [ $# -eq 1 ]; then
    ANTHROPIC_API_KEY=$1
else
    # If not provided as an argument, check if it's set as an environment variable
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "Error: ANTHROPIC_API_KEY is not set. Please provide it as an argument or set it as an environment variable."
        exit 1
    fi
fi

# Check if the 'anthropic' secret already exists
if ! bentoml secret list | awk '{print $1}' | grep -q "^anthropic$"; then
    echo "Creating 'anthropic' secret..."
    bentoml secret create anthropic ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
else
    echo "'anthropic' secret already exists. Skipping creation."
fi

bentoml deploy . --secret anthropic