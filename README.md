# Airlock

Airlock is a small FastAPI-based service for running open-model inference through a single, secure API.

The main idea is simple: **your application talks to Airlock, and Airlock decides which model backend should handle the request.**

This means the rest of your application does not need to know whether the response came from:

* **Mock** — a deterministic local backend, useful for development and testing.
* **Ollama** — runs a real open model locally on your machine.
* **OpenAI-compatible API** — connects to hosted providers such as Groq.

All three backends use the same `/v1` API contract, so you can switch providers without changing the client application.

Airlock also includes a few features that are useful in a production-style inference gateway:

* JWT authentication
* Request validation with Pydantic v2
* Rate limiting
* Usage tracking
* Tool calling
* Structured-output retry handling
* Docker support
* GitHub Actions for linting and tests
* A small Streamlit UI for trying the service manually

---

## What does Airlock actually do?

Think of Airlock as a **security and control layer between your application and an LLM**.

Instead of your frontend directly calling Ollama, Groq, or another model provider:

```text
Frontend
   |
   v
Airlock API
   |
   +----> Mock
   |
   +----> Ollama
   |
   +----> OpenAI-compatible provider
```

Your application always talks to Airlock.

For example:

```text
POST /v1/chat/completions
```

Airlock:

1. Checks the JWT token.
2. Validates the request using Pydantic.
3. Applies rate limits.
4. Selects the configured model provider.
5. Sends the request to that provider.
6. Handles tool calls or structured-output retries if required.
7. Returns a consistent response to the client.
8. Records usage information.

This makes the provider replaceable without changing the API exposed to your application.

---

# Why use a Mock provider?

The default provider is `mock`.

This is intentional.

You should be able to clone the repository and run the complete API **without having a GPU, Ollama, or an external API key**.

For example:

```bash
PROVIDER=mock
```

The mock provider returns deterministic responses, which makes it useful for:

* Unit tests
* CI/CD
* Local development
* API development
* Demonstrations
* Machines without GPUs

Once the API is working, you can switch to a real model.

---

# Requirements

Before starting, make sure you have:

* Python 3.11+
* `pip`
* Git
* Optional: Ollama, if you want to run a local model
* Optional: a Groq API key, if you want to use a hosted model

Docker is also supported, but it is not required for the basic setup.

---

# Quick Start

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd airlock
```

## 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

---

## 3. Install Airlock

Install the development and UI dependencies:

```bash
pip install -e ".[dev,ui]"
```

The `-e` option installs the project in editable mode, so changes to the source code are immediately available without reinstalling the package.

---

## 4. Create your environment file

```bash
cp .env.example .env
```

Open `.env` and review the configuration.

For local development, you can start with the default mock provider.

---

## 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

The API should now be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

You can open `/docs` in your browser and try the API without writing any additional client code.

---

# Demo Login

The example configuration contains a development login:

```text
Username: demo
Password: demo-pass
```

These credentials are only intended for local development.

Before exposing Airlock to anyone else:

1. Change the username/password.
2. Generate a strong `JWT_SECRET`.
3. Set:

```text
ENVIRONMENT=prod
```

Airlock will refuse to start in production if the JWT secret is still the development default.

---

# Starting the Streamlit UI

Airlock includes a small Streamlit application so you can interact with the API from a browser.

Keep the FastAPI server running in the first terminal.

Open another terminal:

```bash
source .venv/bin/activate
streamlit run streamlit_app/app.py
```

Streamlit will print the URL where the UI is available.

The UI lets you:

* Log in
* Send chat requests
* Enable tools
* Test structured output
* View responses
* See the provider being used

The Streamlit application is intentionally kept outside the FastAPI service process. It behaves like a normal client consuming the API.

---

# Using the API directly

If you don't want to use the Streamlit UI, there is a demo script:

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

This is useful when you want to see the API flow directly from the command line.

You can also use the interactive FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Authentication

Airlock protects inference and usage endpoints with JWT authentication.

The basic flow is:

```text
Client
  |
  | username + password
  v
POST /v1/auth/token
  |
  | JWT
  v
Client
  |
  | Authorization: Bearer <token>
  v
Protected API endpoints
```

This prevents someone from calling the inference endpoints without first authenticating.

For example, the client receives a JWT from:

```text
POST /v1/auth/token
```

Then sends it with subsequent requests:

```http
Authorization: Bearer <token>
```

The inference and usage routes require this token.

---

# Request Validation

Airlock uses **Pydantic v2** for request and response schemas.

This means invalid requests are rejected before they reach the model provider.

For example, if an endpoint expects:

```json
{
  "message": "Hello"
}
```

and the client sends an invalid payload, FastAPI/Pydantic returns a validation error instead of sending the bad request to the model.

Airlock also rejects unknown fields.

This is useful because it catches mistakes early and keeps the API contract predictable.

---

# Model Providers

Airlock supports three provider types.

## 1. Mock

The default provider:

```text
PROVIDER=mock
```

Use this when:

* Developing the API
* Running tests
* Running CI
* You don't have a GPU
* You don't have an external API key

No model download is required.

---

## 2. Ollama

Ollama allows you to run an open model locally.

First install Ollama and download a model:

```bash
ollama pull llama3.2
```

Then start Airlock:

```bash
PROVIDER=ollama \
OLLAMA_MODEL=llama3.2 \
uvicorn app.main:app --port 8000
```

The request flow becomes:

```text
Client
   |
   v
Airlock
   |
   v
Ollama
   |
   v
llama3.2
```

The client still uses the same Airlock API.

It does not need to know that Ollama is being used underneath.

---

# Running Ollama with Docker

Airlock also includes Docker Compose configuration for running Ollama alongside the API.

Start the local profile with:

```bash
PROVIDER=ollama docker compose --profile local up --build
```

Then download the model inside the Ollama container:

```bash
docker compose exec ollama ollama pull llama3.2
```

This is useful when you want a more self-contained local environment.

---

# 3. OpenAI-Compatible Providers

Airlock can also communicate with providers that expose an OpenAI-compatible API.

For example, you can use a hosted provider such as Groq.

Set:

```bash
PROVIDER=openai_compatible
OPENAI_API_KEY=your-key
```

Then start Airlock:

```bash
PROVIDER=openai_compatible \
OPENAI_API_KEY=your-key \
uvicorn app.main:app --port 8000
```

The exact model name can change over time, so check the provider's console/documentation for the currently supported model.

The important part is that your application still talks to Airlock rather than directly depending on the provider.

---

# Switching Providers

One of the main ideas behind Airlock is that the client API does not need to change when the model backend changes.

For example:

```text
Development
    |
    +--> Mock
```

Then:

```text
Local testing
    |
    +--> Ollama
    |
    +--> llama3.2
```

And later:

```text
Hosted inference
    |
    +--> OpenAI-compatible provider
    |
    +--> Groq
```

The API contract stays the same.

You mainly change configuration:

```text
PROVIDER=mock
```

or:

```text
PROVIDER=ollama
```

or:

```text
PROVIDER=openai_compatible
```

---

# Tool Calling

Airlock contains a small tool loop to demonstrate how an inference gateway can handle tool calls.

For example, try asking:

```text
How many tokens are in hello airlock?
```

with tools enabled.

The flow looks roughly like:

```text
User request
     |
     v
Model
     |
     | requests a tool
     v
Airlock tool loop
     |
     | executes tool
     v
Tool result
     |
     v
Model
     |
     v
Final response
```

The API response also exposes a `tool_trace`.

This makes it easier to understand what happened between the initial request and the final model response.

---

# Structured Output

Airlock also demonstrates structured-output handling.

Instead of asking the model for free-form text, the application can request a specific structure.

For example, given:

```text
Please fix the login bug today, this is urgent.
```

Airlock can extract structured information such as:

```json
{
  "priority": "high"
}
```

If the first model response does not match the expected structure, Airlock can retry the request using the required format.

This is a common pattern in production LLM applications because applications usually need predictable data rather than arbitrary model text.

---

# Rate Limiting

Airlock includes rate limiting so clients cannot make unlimited inference requests.

This is especially important for hosted models because every request can consume:

* Model capacity
* API quota
* Tokens
* Money

The rate-limit layer sits before the model provider, so requests can be rejected before they reach the expensive part of the system.

---

# Usage Tracking

Airlock exposes usage information through:

```text
/v1/usage
```

This gives you a simple way to inspect inference usage and understand which provider is currently being used.

For a production gateway, this type of information can eventually be extended to include:

* Request counts
* Token usage
* Per-user usage
* Provider usage
* Latency
* Errors
* Cost estimation

---

# Project Structure

The repository is organized by responsibility:

```text
airlock/
│
├── app/
│   │
│   ├── api/
│   │   └── v1/
│   │       └── Versioned HTTP API
│   │
│   ├── auth/
│   │   └── JWT authentication
│   │
│   ├── schemas/
│   │   └── Pydantic request/response models
│   │
│   ├── services/
│   │   ├── inference
│   │   ├── tools
│   │   ├── prompts
│   │   ├── rate limiting
│   │   └── usage tracking
│   │
│   └── providers/
│       ├── mock
│       ├── Ollama
│       └── OpenAI-compatible
│
├── streamlit_app/
│   └── Small web client for Airlock
│
├── scripts/
│   └── demo.sh
│
├── docs/
│   ├── architecture.md
│   ├── api-contracts.md
│   └── learning-map.md
│
├── .env.example
├── docker-compose.yml
└── ...
```

The separation is intentional.

For example, provider-specific code should stay inside `providers/` rather than spreading Ollama or Groq logic throughout the API.

---

# Architecture

At a high level:

```text
                         ┌─────────────────┐
                         │   Streamlit UI  │
                         └────────┬────────┘
                                  │
                                  │ HTTP + JWT
                                  ▼
                         ┌─────────────────┐
                         │   FastAPI API   │
                         │      /v1        │
                         └────────┬────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
             Auth/JWT       Validation        Rate Limit
                 │                │                │
                 └────────────────┼────────────────┘
                                  ▼
                         ┌─────────────────┐
                         │ Inference Layer │
                         └────────┬────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
        ┌─────────┐          ┌─────────┐       ┌──────────────┐
        │  Mock   │          │ Ollama  │       │ OpenAI       │
        │         │          │         │       │ Compatible   │
        └─────────┘          └────┬────┘       └──────────────┘
                                  │
                                  ▼
                              Local Model
```

The important architectural decision is that the API layer does not need to know the implementation details of each provider.

---

# Documentation

More detailed documentation is available in the `docs/` directory.

### Architecture

Read:

```text
docs/architecture.md
```

This explains how the major components fit together.

### API Contracts

Read:

```text
docs/api-contracts.md
```

This documents the HTTP endpoints and request/response formats.

### Learning Map

Read:

```text
docs/learning-map.md
```

This is useful if you're using Airlock as a learning project and want to understand the concepts in the order they appear in the codebase.

---

# Running Tests

Run the linter and formatter check:

```bash
ruff check .
ruff format --check .
```

Then run the test suite:

```bash
pytest
```

Or run everything together:

```bash
make test
```

`make test` performs the same checks after the project dependencies have been installed.

---

# Production Configuration

Airlock is designed primarily as a demonstration/learning service, but it includes a few production-oriented safeguards.

Before deploying it anywhere shared:

### Change the development credentials

Do not use:

```text
demo / demo-pass
```

for a real deployment.

### Set a strong JWT secret

Use a randomly generated secret of at least 32 bytes.

For example, generate one with Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then put the generated value in:

```text
JWT_SECRET=...
```

### Use production mode

```text
ENVIRONMENT=prod
```

Airlock will refuse to start if the JWT secret is still the development default.

### Protect your API key

If using a hosted provider:

```text
OPENAI_API_KEY=...
```

should be stored as a secret and should never be committed to Git.
