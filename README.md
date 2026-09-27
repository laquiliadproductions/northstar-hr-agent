# Northstar HR Agent

Northstar HR Agent is an agentic AI application for HR policy and operations tasks. It uses Retrieval-Augmented Generation (RAG), internal policy documents, mock employee data, and Model Context Protocol (MCP) tools to produce grounded responses with source citations.

## Features

- Search internal HR policy documents
- Generate answers grounded in retrieved content
- Cite the source documents used
- Plan tasks and select tools through an AI agent
- Retrieve mock employee, PTO, and benefits data
- Connect to one or more MCP servers
- Evaluate retrieval and response quality

## Technology Stack

- Python 3.12
- Streamlit
- LangChain and LangGraph
- ChromaDB
- OpenAI-compatible models
- Model Context Protocol Python SDK
- Pytest

## Setup

Clone the repository and enter the project directory:

    git clone REPOSITORY_URL
    cd northstar-hr-agent

Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install the dependencies:

    python -m pip install -r requirements.txt

Copy the example environment file:

    cp .env.example .env

Add the required API keys to .env. Never commit the .env file.

## Local Run

Activate the environment and start the application:

    source .venv/bin/activate
    streamlit run app.py

Open the URL displayed by Streamlit.

## Testing

Run the automated tests:

    pytest -q

## Evaluation

The evaluation process tests retrieval relevance, response grounding, citation accuracy, tool selection, MCP execution, and task completion.

Run the evaluation suite:

    python evaluation/run_evaluation.py

## Deployment

The application is intended for a free-tier host such as Render or Railway.

Install command:

    pip install -r requirements.txt

Start command:

    streamlit run app.py --server.address 0.0.0.0 --server.port $PORT

Configure API keys through the hosting provider's environment-variable settings. Do not store secrets in the repository.

## Reproducibility

- Dependencies are pinned in requirements.txt.
- Random seeds will be fixed where applicable.
- Document chunking settings will be explicitly configured.
- Evaluation sampling will be deterministic.
- Secrets will be read from environment variables.

## Security

Never commit API keys, passwords, tokens, .env, .venv, or real employee personal information. All employee records used by this project are fictional.
