# enterprise-ai-search-platform — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

This is a local laptop proof. It does not call a hosted model and it does not apply production changes.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/entsearch/__init__.py"]
    M1["src/entsearch/answer.py"]
    M2["src/entsearch/main.py"]
    M3["src/entsearch/ops.py"]
    M2 -->|imports| M1
    M2 -->|imports| M3
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/entsearch/main.py`](src/entsearch/main.py) | HTTP handlers: `GET /healthz`, `POST /ask` |
| [`src/entsearch/ops.py`](src/entsearch/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/entsearch/answer.py`](src/entsearch/answer.py) | Functions: `words`, `answer` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/entsearch/__init__.py`](src/entsearch/__init__.py) | Implementation or supporting configuration |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_ask.py`](tests/test_ask.py) | Executable checks and regression examples |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

## Existing design and operating guides

These checked-in guides provide the project’s detailed design, operational context, or deployment view:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/entsearch/main.py`](src/entsearch/main.py#L10) |
| `POST /ask` | `post_ask` | [`src/entsearch/main.py`](src/entsearch/main.py#L15) |
| `GET /readyz` | `readyz` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L44) |
| `POST /workspaces` | `create_workspace` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L49) |
| `GET /workspaces` | `list_workspaces` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L66) |
| `POST /workspaces/{workspace_id}/jobs` | `create_job` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L73) |
| `GET /jobs/{job_id}` | `get_job` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L96) |
| `POST /jobs/{job_id}/approve` | `approve_job` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L105) |
| `GET /audit` | `audit` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L122) |
| `GET /metrics` | `metrics` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L138) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `answer(question, source=None)`

Source: [`src/entsearch/answer.py`](src/entsearch/answer.py#L16).

Calls visible in this function: `InputError`, `isinstance`, `len`, `question.strip`, `ranked.append`, `ranked.sort`, `words`.

```python
def answer(question, source=None):
    if not isinstance(question, str) or not question.strip():
        raise InputError("question is empty")
    corpus = PASSAGES
    if source is not None:
        corpus = [item for item in corpus if item[0] == source]
        if not corpus:
            raise InputError(f"unknown source: {source}")
    query = words(question)
    ranked = []
    for name, text in corpus:
        overlap = query & words(text)
        ranked.append({"source": name, "text": text, "overlap": len(overlap)})
    ranked.sort(key=lambda row: (-row["overlap"], row["source"]))
    best = ranked[0]
    if best["overlap"] < MIN_OVERLAP:
        return {"answered": False, "answer": "No passage shares enough terms.", "citation": None, "passages": ranked}
    return {"answered": True, "answer": best["text"], "citation": best["source"], "passages": ranked}
```

### `words(text)`

Source: [`src/entsearch/answer.py`](src/entsearch/answer.py#L12).

Calls visible in this function: `re.findall`, `set`, `text.lower`.

```python
def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP
```

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `InputError('question is empty')` | [`src/entsearch/answer.py`](src/entsearch/answer.py#L18) |
| `InputError(f'unknown source: {source}')` | [`src/entsearch/answer.py`](src/entsearch/answer.py#L23) |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/entsearch/main.py`](src/entsearch/main.py#L19) |
| `HTTPException(status_code=404, detail='workspace not found')` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L77) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L100) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L109) |
| `HTTPException(status_code=403, detail='production apply is disabled in this lab')` | [`src/entsearch/ops.py`](src/entsearch/ops.py#L113) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/entsearch/answer.py`](src/entsearch/answer.py) defines module-level containers: `STOP`, `PASSAGES`.
- [`src/entsearch/ops.py`](src/entsearch/ops.py) defines module-level containers: `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `answer`

In [`src/entsearch/answer.py`](src/entsearch/answer.py#L16), `answer(question, source=None)` receives the inputs. The function computes these intermediate values:

- `corpus = PASSAGES`
- `query = words(question)`
- `ranked = []`
- `best = ranked[0]`

Its result is defined by:

- `{'answered': True, 'answer': best['text'], 'citation': best['source'], 'passages': ranked}`
- `{'answered': False, 'answer': 'No passage shares enough terms.', 'citation': None, 'passages': ranked}`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/entsearch/answer.py`](src/entsearch/answer.py#L16) branches on:

- `not isinstance(question, str) or not question.strip()`
- `source is not None`
- `best['overlap'] < MIN_OVERLAP`
- `not corpus`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

### What does the operations plane add, and where is its limit

[`src/entsearch/ops.py`](src/entsearch/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_ask.py`](tests/test_ask.py), [`tests/test_ops.py`](tests/test_ops.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
