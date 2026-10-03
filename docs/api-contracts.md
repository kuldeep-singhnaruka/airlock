# Airlock API Contracts

This document describes the HTTP API exposed by Airlock.

The goal is to keep the API predictable: clients should know **which endpoint to call, what to send, what they will receive, and what errors to expect**.

---

## 1. Base URL

When running Airlock locally:

```text
http://127.0.0.1:8000
```

All application endpoints are versioned under:

```text
/v1
```

For example:

```text
POST /v1/chat
GET  /v1/models
GET  /v1/usage
```

### Why use `/v1`?

The version prefix protects existing clients from unexpected breaking changes.

If a future version needs to make a breaking change to a request or response, it should be introduced under:

```text
/v2
```

instead of silently changing the existing `/v1` contract.

---

# 2. Authentication

Most Airlock endpoints require a JWT access token.

The client must send:

```http
Authorization: Bearer <access_token>
```

The following endpoints do **not** require authentication:

```text
GET  /health
POST /v1/auth/token
```

Everything else requires a valid JWT.

### Request flow

The normal flow is:

```text
1. Login
      |
      v
POST /v1/auth/token
      |
      v
Receive JWT
      |
      v
Send JWT with API requests
      |
      v
Protected endpoint
```

For example:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

# 3. General Validation Rules

Airlock uses Pydantic v2 to validate incoming requests.

This means invalid requests are rejected **before they reach the model provider**.

## Unknown fields are rejected

For example, if `/v1/chat` expects:

```json
{
  "messages": [],
  "temperature": 0.2
}
```

sending an unexpected field such as:

```json
{
  "messages": [],
  "temperature": 0.2,
  "something_random": true
}
```

will result in a validation error.

This helps catch client-side mistakes early.

---

## Strings are stripped

Authentication and extraction models strip leading and trailing whitespace from strings.

For example:

```json
{
  "username": "  demo  ",
  "password": "demo-pass"
}
```

is treated as:

```json
{
  "username": "demo",
  "password": "demo-pass"
}
```

This avoids unnecessary failures caused by accidental spaces.

---

# 4. GET `/health`

Checks whether the Airlock service is running.

### Authentication

No authentication required.

### Request

```http
GET /health
```

### Example response

```json
{
  "status": "ok",
  "service": "airlock",
  "provider": "mock",
  "model": "mock-model",
  "version": "0.1.0"
}
```

### What the response tells you

| Field      | Meaning                             |
| ---------- | ----------------------------------- |
| `status`   | Current service status              |
| `service`  | Service name                        |
| `provider` | Currently configured model provider |
| `model`    | Currently configured model          |
| `version`  | Airlock API/service version         |

This endpoint is intentionally public so health checks can be performed without a JWT.

---

# 5. POST `/v1/auth/token`

Creates a JWT access token.

This is the endpoint a client uses to log in.

### Authentication

No JWT required.

### Request

```http
POST /v1/auth/token
Content-Type: application/json
```

```json
{
  "username": "demo",
  "password": "demo-pass"
}
```

### Successful response

Status:

```text
200 OK
```

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

The client should store the returned `access_token` and send it with subsequent requests.

---

## Invalid login

If the username or password is incorrect:

```text
401 Unauthorized
```

is returned.

---

## JWT contents

The token contains:

```text
sub
exp
```

Where:

* `sub` identifies the authenticated user.
* `exp` contains the token expiration time.

The token is signed using:

```text
JWT_SECRET
```

with:

```text
HS256
```

---

# 6. POST `/v1/chat`

This is the main inference endpoint.

Use it when you want to send a conversation to the configured model provider.

### Authentication

Required.

```http
Authorization: Bearer <access_token>
```

---

## Request

```http
POST /v1/chat
Content-Type: application/json
Authorization: Bearer <access_token>
```

Example:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "How many tokens are in hello airlock?"
    }
  ],
  "temperature": 0.2,
  "max_tokens": 256,
  "enable_tools": true
}
```

---

## Request fields

### `messages`

List of conversation messages.

The list must contain between:

```text
1 and 20 messages
```

Each message has:

```text
role
content
```

Supported roles are:

```text
system
user
assistant
```

Example:

```json
{
  "role": "user",
  "content": "Hello Airlock"
}
```

---

### `temperature`

Controls how much variation the model can introduce into its response.

Allowed range:

```text
0 to 2
```

Example:

```json
"temperature": 0.2
```

A lower value generally makes responses more deterministic.

---

### `max_tokens`

Maximum number of completion tokens requested from the provider.

Allowed range:

```text
1 to 1024
```

Example:

```json
"max_tokens": 256
```

---

### `enable_tools`

Controls whether Airlock's built-in tools are available during the request.

Example:

```json
"enable_tools": true
```

If tools are disabled, the model cannot use the Airlock tool loop.

---

# 7. Chat Response

A successful request returns:

```text
200 OK
```

Example:

```json
{
  "id": "chat_...",
  "model": "mock-model",
  "content": "Tool finished. Tool result for estimate_tokens: {...}",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  },
  "tool_trace": [
    {
      "name": "estimate_tokens",
      "arguments": {
        "text": "How many tokens are in hello airlock?"
      },
      "result": "{\"estimated_tokens\":10,\"method\":\"chars/4\"}"
    }
  ]
}
```

### Response fields

| Field        | Meaning                       |
| ------------ | ----------------------------- |
| `id`         | Unique ID for the request     |
| `model`      | Model used for the response   |
| `content`    | Final model response          |
| `usage`      | Token usage information       |
| `tool_trace` | Tools used during the request |

---

# 8. Chat Tools

When:

```json
"enable_tools": true
```

Airlock makes two built-in tools available.

## `estimate_tokens`

Estimates the number of tokens in a piece of text.

### Argument

```json
{
  "text": "Hello Airlock"
}
```

### Result

The current implementation uses:

```text
characters / 4
```

as an approximation.

For example:

```json
{
  "estimated_tokens": 10,
  "method": "chars/4"
}
```

This is only an estimate, not an exact tokenizer result.

---

## `model_card`

Returns information about a model.

### Argument

```json
{
  "model_name": "mock-model"
}
```

The result contains information such as:

* Context window
* Short usage information

---

# 9. Tool Loop Limit

Airlock does not allow the model to call tools forever.

The service limits the number of provider calls using:

```text
MAX_TOOL_ROUNDS
```

The default is:

```text
3
```

Conceptually:

```text
User
 |
 v
Model
 |
 | tool request
 v
Tool
 |
 v
Model
 |
 | tool request
 v
Tool
 |
 v
Model
 |
 v
Final response
```

Once the maximum number of rounds is reached, Airlock stops the loop.

If the tool loop cannot finish successfully, the API returns:

```text
502 Bad Gateway
```

---

# 10. POST `/v1/extract`

Extracts structured information from plain text.

This endpoint is useful when you want predictable JSON rather than a free-form model response.

### Authentication

Required.

---

## Request

```http
POST /v1/extract
Content-Type: application/json
Authorization: Bearer <access_token>
```

Example:

```json
{
  "text": "Please fix the login bug today, this is urgent",
  "schema_name": "task"
}
```

---

# 11. Supported Extraction Schemas

Airlock currently supports:

```text
task
sentiment
```

---

## Task extraction

Request:

```json
{
  "text": "Please fix the login bug today, this is urgent",
  "schema_name": "task"
}
```

Example result:

```json
{
  "title": "Please fix the login bug today, this is urgent",
  "priority": "high",
  "tags": [
    "extracted"
  ]
}
```

### `priority`

Allowed values:

```text
low
medium
high
```

---

## Sentiment extraction

Request:

```json
{
  "text": "The new login experience is great!",
  "schema_name": "sentiment"
}
```

Example result:

```json
{
  "label": "positive",
  "confidence": 0.9,
  "rationale": "The text uses positive language."
}
```

### `label`

Allowed values:

```text
positive
neutral
negative
```

### `confidence`

Must be between:

```text
0 and 1
```

For example:

```json
"confidence": 0.9
```

means the model is reporting 90% confidence in its classification.

---

# 12. Structured Output Retry

The model is expected to return JSON matching the selected schema.

For example, when:

```text
schema_name = task
```

the response must match the task schema.

If the model returns invalid JSON or JSON that does not match the schema, Airlock sends the validation error back into the retry flow.

The gateway retries **once**.

The flow is:

```text
Request
   |
   v
Model attempt #1
   |
   +---- valid JSON ------> Return result
   |
   +---- invalid JSON
             |
             v
       Validation error
             |
             v
       Model attempt #2
             |
             +---- valid ------> Return result
             |
             +---- invalid ---> 422
```

If both attempts fail validation, the API returns:

```text
422 Unprocessable Entity
```

The `usage` information includes both attempts.

---

# 13. GET `/v1/models`

Returns information about the currently configured provider and model.

### Authentication

Required.

### Request

```http
GET /v1/models
Authorization: Bearer <access_token>
```

### Response

```json
{
  "provider": "mock",
  "model": "mock-model",
  "tools": [
    "estimate_tokens",
    "model_card"
  ]
}
```

This is useful for clients that need to know what provider/model is currently available.

### Rate limiting

This endpoint is rate limited.

---

# 14. GET `/v1/usage`

Returns usage information for the authenticated user.

### Authentication

Required.

### Request

```http
GET /v1/usage
Authorization: Bearer <access_token>
```

### Example response

```json
{
  "username": "demo",
  "requests": 2,
  "prompt_tokens": 20,
  "completion_tokens": 10,
  "total_tokens": 30
}
```

### Important

Usage counters are stored in process memory.

That means:

```text
Application running
       |
       v
Usage is tracked
       |
       v
Application restarts
       |
       v
Counters reset
```

This is suitable for the current demo/service design but would normally be replaced with persistent storage in a production system.

---

## Why isn't `/v1/usage` rate limited?

The usage endpoint is intentionally not rate limited.

This means that even if a client receives:

```text
429 Too Many Requests
```

from an inference endpoint, it can still check its usage.

For example:

```text
POST /v1/chat
       |
       v
429 Too Many Requests
       |
       v
GET /v1/usage
       |
       v
Check current usage
```

---

# 15. Common Errors

Airlock uses standard HTTP status codes to communicate failures.

| Status | Meaning                                   |
| ------ | ----------------------------------------- |
| `401`  | Authentication failed                     |
| `422`  | Request or model output failed validation |
| `429`  | Rate limit exceeded                       |
| `502`  | Provider or tool-loop failure             |

---

## 401 — Unauthorized

Returned when:

* JWT is missing
* JWT is invalid
* JWT has expired
* JWT cannot be verified
* Login credentials are incorrect

Example:

```text
401 Unauthorized
```

---

## 422 — Validation Error

Returned when:

* Request data does not match the API schema
* Required fields are missing
* Values are outside their allowed range
* Unknown fields are supplied
* Structured model output fails validation twice

For example:

```json
{
  "temperature": 5
}
```

would fail because the allowed range is:

```text
0 <= temperature <= 2
```

---

## 429 — Too Many Requests

Returned when the client exceeds the configured inference rate limit.

The response includes:

```http
Retry-After: <seconds>
```

The client should wait for the specified amount of time before trying again.

The limit is controlled by:

```text
RATE_LIMIT_REQUESTS
```

and the configured rate-limit window.

---

## 502 — Bad Gateway

This normally means Airlock could not successfully complete an operation involving the provider.

Examples include:

* Provider transport failure
* Model provider unavailable
* Tool loop exceeded its allowed execution
* Tool execution could not complete successfully

The client should treat this as a gateway/provider-side failure rather than a request validation problem.

---

# 16. Request IDs

Every API response includes:

```http
x-request-id: <request-id>
```

This ID is useful when debugging.

For example:

```text
x-request-id: 7d9b3f3e-...
```

If something goes wrong, include this ID when checking logs.

The gateway can generate the ID automatically if the client does not provide one.

This gives you a simple way to connect:

```text
Client request
      |
      v
API response
      |
      v
x-request-id
      |
      v
Application logs
```

---

# 17. Complete API Overview

| Method | Endpoint         | Auth | Rate Limited | Purpose                        |
| ------ | ---------------- | ---: | -----------: | ------------------------------ |
| `GET`  | `/health`        |   No |           No | Check service health           |
| `POST` | `/v1/auth/token` |   No |           No | Login and receive JWT          |
| `POST` | `/v1/chat`       |  Yes |          Yes | Run model inference            |
| `POST` | `/v1/extract`    |  Yes |          Yes | Extract structured data        |
| `GET`  | `/v1/models`     |  Yes |          Yes | Get provider/model information |
| `GET`  | `/v1/usage`      |  Yes |           No | View current usage             |

---

# 18. Typical Client Flow

A normal client interaction looks like this:

```text
                     AIRLOCK API

  ┌─────────────┐
  │    Client   │
  └──────┬──────┘
         │
         │ 1. Login
         ▼
  ┌──────────────────┐
  │ POST /v1/auth/   │
  │      token       │
  └────────┬─────────┘
           │
           │ JWT
           ▼
  ┌──────────────────┐
  │  POST /v1/chat   │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Authentication   │
  │ Validation       │
  │ Rate limiting    │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Inference layer  │
  └────────┬─────────┘
           │
       ┌───┴───────────────┐
       │                   │
       ▼                   ▼
    Ollama              Hosted API
       │                   │
       └─────────┬─────────┘
                 ▼
             Response
                 │
                 ▼
              Client
```

The important part is that the client only needs to understand the Airlock API.

The underlying model provider can be changed without changing the client's `/v1` contract.

---

# 19. Quick Reference

### Check the service

```bash
curl http://127.0.0.1:8000/health
```

### Login

```text
POST /v1/auth/token
```

### Send a chat request

```text
POST /v1/chat
```

### Extract structured information

```text
POST /v1/extract
```

### Check the configured model

```text
GET /v1/models
```

### Check usage

```text
GET /v1/usage
```

### Interactive API documentation

```text
http://127.0.0.1:8000/docs
```

---

## The main idea

The API is intentionally small.

A client mainly needs to remember four things:

1. **Login first** and get a JWT.
2. **Send the JWT** with protected requests.
3. **Use `/v1/chat` or `/v1/extract`** for inference.
4. **Use `/v1/usage` and `x-request-id`** when monitoring or debugging.

Everything behind those endpoints — authentication, validation, tools, retries, rate limiting, usage tracking, and the actual model provider — is handled by Airlock.
