# Airlock — Day 6–10 Learning Map

This part of the project is designed as a hands-on learning path.

The idea is simple:

> **Don't just read the code. Study one concept, find where it is implemented, then make a small change and verify that the application still works.**

Each day builds on the previous days, so by Day 10 you should understand how a request travels from the API all the way to the model provider and back.

---

# How to use this guide

For each day:

1. Read the listed files.
2. Understand what problem the code is solving.
3. Run the existing tests before changing anything.
4. Complete the exercise.
5. Run the tests again.
6. Try the feature manually if possible.
7. Be able to explain **why the code is structured that way**.

You do not need to memorize every line.

The goal is to understand the boundaries between:

```text
API
  ↓
Validation
  ↓
Authentication
  ↓
Service logic
  ↓
Tools / prompts
  ↓
Model provider
  ↓
Response validation
```

---

# Day 6 — Advanced Python

## Main goal

Understand how Python features are being used to make the service safer, configurable, and easier to maintain.

### Topics

| Concept                    | Where to look             |
| -------------------------- | ------------------------- |
| Strict request models      | `app/schemas/`            |
| `extra="forbid"`           | `app/schemas/`            |
| Validation bounds          | `app/schemas/`            |
| Environment-based settings | `app/config.py`           |
| Async HTTP clients         | `app/providers/ollama.py` |
| Python packaging           | `pyproject.toml`          |
| Separate UI process        | `streamlit_app/app.py`    |

---

## 1. Pydantic request models

Start with:

```text
app/schemas/
```

Look at how request models are defined.

For example, a request might define:

```text
temperature: 0 to 2
max_tokens: 1 to 1024
```

This means invalid data is rejected automatically.

Instead of manually writing:

```python
if temperature < 0:
    ...
```

Pydantic performs the validation for us.

---

## 2. `extra="forbid"`

Look for:

```python
extra="forbid"
```

This tells Pydantic:

> If the client sends a field that isn't part of the API contract, reject the request.

For example:

```json
{
  "temperature": 0.5,
  "unknown_field": true
}
```

should fail validation.

This is important for APIs because silently accepting misspelled or unexpected fields can hide client bugs.

---

## 3. Environment-based configuration

Open:

```text
app/config.py
```

Study how values such as:

```text
PROVIDER
JWT_SECRET
OLLAMA_MODEL
RATE_LIMIT_REQUESTS
```

come from environment variables.

The important concept is:

```text
Code
  |
  | reads configuration
  v
Environment
```

rather than hard-coding environment-specific values into Python.

For example, the same application can run with:

```text
PROVIDER=mock
```

locally and:

```text
PROVIDER=ollama
```

on another machine.

---

## 4. Async HTTP

Open:

```text
app/providers/ollama.py
```

Look at how the provider communicates with Ollama asynchronously.

The important concept is that network calls can take time.

Instead of blocking the entire application while waiting for a response, async I/O allows the server to handle other work while the network operation is in progress.

You don't need to become an async Python expert on Day 6.

Focus on understanding:

```text
async def
await
HTTP request
response
timeout
```

---

## 5. Packaging

Open:

```text
pyproject.toml
```

Understand:

* Project metadata
* Dependencies
* Development dependencies
* UI dependencies
* Test configuration
* Ruff configuration

The important idea is that `pyproject.toml` describes how the Python project should be installed and developed.

---

## Exercise — Add a summary field

Add:

```text
summary
```

to `TaskExtraction`.

For example, the existing result:

```json
{
  "title": "Fix the login bug",
  "priority": "high",
  "tags": ["extracted"]
}
```

could become:

```json
{
  "title": "Fix the login bug",
  "priority": "high",
  "tags": ["extracted"],
  "summary": "Urgent request to fix the login issue today."
}
```

### What you need to change

Find the `TaskExtraction` schema.

Add the new field.

Then update `MockProvider` so it generates a value for `summary`.

Finally, update the relevant schema/test assertions.

### What this exercise teaches

You are learning that changing an API response often requires changes in multiple layers:

```text
Pydantic schema
      ↓
Provider/mock response
      ↓
Service
      ↓
Tests
```

That is an important real-world development pattern.

---

# Day 7 — Inference API Design

## Main goal

Understand how a clean API separates HTTP concerns from application logic.

### Topics

| Concept                   | Where to look                |
| ------------------------- | ---------------------------- |
| Versioned API             | `app/api/v1/`                |
| Authentication dependency | `app/api/deps.py`            |
| Rate-limit dependency     | `app/api/deps.py`            |
| Application errors        | `app/services/errors.py`     |
| HTTP error mapping        | `app/api/v1/inference.py`    |
| Usage tracking            | `app/services/usage.py`      |
| Rate limiting             | `app/services/rate_limit.py` |

---

# 1. Versioned API

Look at:

```text
app/api/v1/
```

The important idea is that the API is explicitly versioned.

Current API:

```text
/v1
```

If a future change breaks an existing contract, it can become:

```text
/v2
```

rather than silently breaking existing clients.

---

# 2. Dependencies

Look at:

```text
app/api/deps.py
```

You'll see authentication and rate limiting being reused as dependencies.

Conceptually:

```text
Request
   |
   v
JWT dependency
   |
   v
Rate-limit dependency
   |
   v
Route
```

This is better than copying authentication code into every endpoint.

---

# 3. Service errors versus HTTP errors

Look at:

```text
app/services/errors.py
```

and:

```text
app/api/v1/inference.py
```

The service raises application-specific errors.

For example:

```text
ModelBackendError
SchemaMismatchError
ToolLoopError
```

The API layer converts them into HTTP status codes.

For example:

```text
ModelBackendError
      ↓
502 Bad Gateway
```

This keeps the service independent from FastAPI.

---

# 4. Usage tracking

Look at:

```text
app/services/usage.py
```

Understand how the application tracks:

```text
requests
prompt tokens
completion tokens
total tokens
```

Also notice that usage is associated with the authenticated user.

The JWT's:

```text
sub
```

claim identifies the user.

---

# Exercise — Add a second user

Add another demo user in the application settings.

For example:

```text
demo
demo-pass
```

and another test user with different credentials.

Then:

1. Log in as user A.
2. Call `/v1/chat`.
3. Check `/v1/usage`.
4. Log in as user B.
5. Call `/v1/chat`.
6. Check `/v1/usage`.
7. Confirm that the usage totals are separate.

You should end up with something conceptually like:

```text
User A
  requests: 2
  tokens: 30

User B
  requests: 1
  tokens: 15
```

### Why does this work?

Because the usage ledger uses the authenticated identity from the JWT:

```text
JWT
 |
 +--> sub = user A
 |
 v
UsageLedger[user A]
```

and:

```text
JWT
 |
 +--> sub = user B
 |
 v
UsageLedger[user B]
```

### Extra exercise

Think about what a real user database would need.

For example:

```text
users
├── id
├── username
├── password_hash
├── created_at
├── disabled
└── ...
```

You don't need to implement it yet.

The goal is to understand what would eventually replace the demo users stored in application configuration.

---

# Day 8 — Production Toolchain

## Main goal

Understand how the application moves from:

```text
"My code works on my laptop"
```

to:

```text
"This project can be tested and packaged consistently."
```

### Topics

| Concept                  | Where to look              |
| ------------------------ | -------------------------- |
| Multi-stage Docker build | `Dockerfile`               |
| Non-root container       | `Dockerfile`               |
| Local Ollama environment | `docker-compose.yml`       |
| CI testing               | `.github/workflows/ci.yml` |
| Local development hooks  | `.pre-commit-config.yaml`  |

---

# 1. Docker

Open:

```text
Dockerfile
```

Study the multi-stage build.

The general idea is:

```text
Builder
   |
   | install dependencies
   v
Application environment
   |
   | copy required files
   v
Small runtime image
```

Also look at the user the container runs as.

Airlock runs as a non-root user.

That is a security improvement because the application doesn't need root privileges to serve HTTP requests.

---

# 2. Docker Compose

Open:

```text
docker-compose.yml
```

Pay particular attention to the local Ollama profile.

The goal is to make it possible to run:

```text
Airlock
   +
Ollama
```

together.

---

# 3. GitHub Actions

Open:

```text
.github/workflows/ci.yml
```

Understand when the workflow runs and what it checks.

A typical CI flow is:

```text
Developer pushes code
        |
        v
GitHub Actions
        |
        +--> Ruff
        |
        +--> Tests
        |
        v
Pass / Fail
```

This means problems can be caught before code is merged.

---

# 4. Pre-commit

Open:

```text
.pre-commit-config.yaml
```

This provides local checks before a commit is created.

The idea is:

```text
Write code
   ↓
git commit
   ↓
pre-commit checks
   ↓
Commit accepted
```

This catches simple formatting and quality issues early.

---

# Exercise — Build the container

First run:

```bash
pytest
```

Make sure the tests pass.

Then build the Docker image:

```bash
docker build -t airlock .
```

Start the container.

Then check:

```bash
curl http://127.0.0.1:8000/health
```

You should receive the health response.

### What you are learning

This exercise connects several concepts:

```text
Python application
       ↓
Dependencies
       ↓
Docker image
       ↓
Running container
       ↓
HTTP endpoint
```

If `/health` works inside the container, you have confirmed that the application can run independently of your local Python environment.

---

# Day 9 — Prompting

## Main goal

Understand that prompts are part of the application's behavior and should be treated as code.

### Topics

| Concept                        | Where to look                                     |
| ------------------------------ | ------------------------------------------------- |
| Chat system prompt             | `CHAT_SYSTEM_PROMPT` in `app/services/prompts.py` |
| Structured-output instructions | `structured_system_prompt`                        |
| JSON Schema in prompts         | `structured_system_prompt`                        |
| Repair prompts                 | `InferenceService.extract`                        |

---

# 1. Chat system prompt

Find:

```text
CHAT_SYSTEM_PROMPT
```

in:

```text
app/services/prompts.py
```

The system prompt provides instructions to the model before the user's message.

Think of the conversation as:

```text
System instructions
        +
User message
        |
        v
      Model
```

The system prompt establishes the behavior expected from the model.

---

# 2. Structured prompts

The structured extraction flow does more than say:

```text
"Return JSON."
```

It also provides the model with the expected schema.

Conceptually:

```text
System prompt
      +
Schema requirements
      +
User text
      |
      v
    Model
      |
      v
    JSON
```

This gives the model more information about the expected structure.

---

# 3. Repair prompt

Models can still return invalid output.

For example, the application might expect:

```json
{
  "priority": "high"
}
```

but the model returns:

```text
The priority is high.
```

The response cannot be parsed as the required structure.

Airlock can then tell the model what validation failed and ask it to try again.

This is the repair step.

---

# Exercise — Change the chat behavior

Change the chat system prompt so that responses must contain **one sentence**.

Then run the API using:

```text
PROVIDER=ollama
```

and compare the behavior with:

```text
PROVIDER=mock
```

### What to observe

Ask the same question using both providers.

Compare:

```text
Mock
  ↓
Does it follow the new instruction?

Ollama
  ↓
Does the real model follow the instruction consistently?
```

This demonstrates an important LLM concept:

> The same prompt does not necessarily produce identical behavior across different models.

The provider abstraction keeps the API the same, but the underlying model behavior can still differ.

---

# Day 10 — LLM Primitives

## Main goal

Understand the core pieces that make an LLM application more than a simple HTTP request.

### Topics

| Concept             | Where to look                                          |
| ------------------- | ------------------------------------------------------ |
| Tool definitions    | `app/services/tools.py`                                |
| Tool execution      | `app/services/tools.py`                                |
| Tool loop           | `InferenceService.chat`                                |
| Structured output   | `POST /v1/extract`                                     |
| Pydantic validation | Extraction schemas                                     |
| Token accounting    | `UsageStats`, provider parsers                         |
| Model configuration | `max_tokens`, `temperature`, `request_timeout_seconds` |

---

# 1. Tool definitions

Open:

```text
app/services/tools.py
```

Look for:

```text
TOOL_SPECS
```

This describes the tools that the model is allowed to request.

For example:

```text
estimate_tokens
model_card
```

A tool has two important parts:

```text
Tool definition
      +
Tool implementation
```

The model needs to know what the tool looks like, while the application needs to know how to actually execute it.

---

# 2. Tool execution

Find:

```text
execute_tool
```

This is where Airlock takes the model's requested tool and executes it locally.

The important distinction is:

```text
Model decides:
"I want to call estimate_tokens."

Application decides:
"Here is how estimate_tokens actually runs."
```

The model does not directly execute Python code.

---

# 3. Provider-agnostic tool loop

The tool loop lives in:

```text
InferenceService.chat
```

This is important because the loop belongs to the application/service layer, not to a specific provider.

The flow is:

```text
Model
  |
  | tool call
  v
Airlock
  |
  | execute tool
  v
Tool result
  |
  v
Model
  |
  v
Final response
```

The same logic can work with:

```text
Mock
Ollama
OpenAI-compatible provider
```

---

# 4. Structured output

The `/v1/extract` endpoint demonstrates another important LLM primitive.

Instead of accepting arbitrary text:

```text
Model
  ↓
"Here is the task..."
```

the application expects a known structure:

```json
{
  "title": "...",
  "priority": "high",
  "tags": []
}
```

Pydantic validates that structure before the application accepts it.

This is the boundary between:

```text
Untrusted model output
        ↓
Validation
        ↓
Application data
```

That boundary is extremely important in real LLM applications.

---

# 5. Token accounting

Airlock tracks:

```text
prompt_tokens
completion_tokens
total_tokens
```

Look at:

```text
UsageStats
```

and the provider response parsers.

This matters because tokens affect:

* Usage
* Cost
* Latencies
* Context limits

A provider may return token usage directly, while another provider may represent it differently.

The provider layer is responsible for normalizing that information before it reaches the rest of the application.

---

# 6. Latency versus quality

Look at:

```text
max_tokens
temperature
request_timeout_seconds
```

These settings influence different aspects of model behavior.

For example:

### `max_tokens`

Controls how much output the model can generate.

Higher:

```text
more possible output
```

Lower:

```text
shorter output
```

---

### `temperature`

Controls response variation.

A lower value generally gives more deterministic behavior.

A higher value allows more variation.

---

### `request_timeout_seconds`

Controls how long Airlock waits for the provider.

A model request is a network operation, so the gateway needs a timeout rather than waiting forever.

---

# Exercise — Add `utc_now`

Add a third tool:

```text
utc_now
```

The tool should take **no arguments**.

---

## Step 1 — Add the tool specification

Register it in:

```text
TOOL_SPECS
```

The model should be told that the tool:

```text
Name: utc_now
Arguments: none
```

---

## Step 2 — Implement the tool

Update:

```text
execute_tool
```

so that:

```text
utc_now
```

returns the current UTC time.

Conceptually:

```text
utc_now()
   |
   v
Current UTC timestamp
```

---

## Step 3 — Update the mock provider

Teach the mock provider that a prompt such as:

```text
what time is it
```

should request:

```text
utc_now
```

---

## Step 4 — Test it

Send a request such as:

```text
What time is it?
```

with tools enabled.

You should be able to see the tool request in:

```text
tool_trace
```

and see the resulting time.

---

# What You Should Understand After Day 10

By the end of these exercises, you should be able to explain the complete request lifecycle.

For example:

```text
                    CLIENT
                       |
                       v
              POST /v1/chat
                       |
                       v
              ┌────────────────┐
              │ FastAPI Router │
              └───────┬────────┘
                      |
              ┌───────┴────────┐
              │                │
              v                v
          JWT Auth        Rate Limiter
              │                │
              └───────┬────────┘
                      v
             ┌──────────────────┐
             │ InferenceService │
             └────────┬─────────┘
                      |
          ┌───────────┼───────────┐
          v           v           v
       Prompts      Tools      Validation
          |           |           |
          └───────────┼───────────┘
                      v
               ModelProvider
                      |
             ┌────────┼────────┐
             v        v        v
           Mock    Ollama   Hosted API
                      |
                      v
                  Model output
                      |
                      v
                  Validation
                      |
                      v
                 Usage Ledger
                      |
                      v
                    Client
```

The important part is not memorizing the diagram.

You should understand **why the boundaries exist**.

---

# What to Say in the Demo

The main point of the demo is the architecture boundary.

A good explanation is:

> "The client always talks to the same `/v1` API. The API doesn't need to know whether the model is fake, running locally through Ollama, or running through a hosted provider."

Then explain the two important protections:

> "JWT authentication and Pydantic validation sit at the edge of the service, so unauthenticated or malformed requests are rejected before they reach the model."

Then explain the model-side controls:

> "Tools, structured-output validation, and repair logic sit close to the model call. That gives us a place to validate and control model output before it becomes application data."

Finally, demonstrate the provider switch:

```text
PROVIDER=mock
```

then:

```text
PROVIDER=ollama
```

and explain:

> "The provider changed, but the client-facing API did not."

---

# The Big Picture

The Day 6–10 journey is essentially:

```text
Day 6
Python foundations
       ↓
Day 7
API architecture
       ↓
Day 8
Packaging + deployment
       ↓
Day 9
Prompt engineering
       ↓
Day 10
LLM tools + structured output
```

By the end, you should not just know how to run Airlock.

You should be able to explain:

* Why Pydantic is used
* Why JWT authentication is separate from inference
* Why the API is versioned
* Why provider-specific code is isolated
* Why a mock provider is useful
* How tool calling works
* How structured output is validated
* Why model output should not be trusted blindly
* How usage is tracked
* Why in-memory state limits horizontal scaling
* How Docker packages the service
* Why prompts belong in a dedicated layer
* How the same API can work with completely different model backends

That is the real objective of Days 6–10: **understand the design decisions, not just the code.**
