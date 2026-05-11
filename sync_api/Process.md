---

# 📘Phase 1 & Phase 2

---

## Project: Asynchronous Task Scheduler API (Django)

This project incrementally builds an async-ready backend API for handling long-running tasks (web scraping), focusing on **correct API design before concurrency**.

---

## Phase 1 — Synchronous Task Execution (Baseline)

### Goal

Establish a clean, testable baseline where:

* A URL is accepted via API
* The page is scraped synchronously
* Results are stored in the database

### What Happens
# and been 
```
POST /get_data/
→ scrape URL synchronously
→ store result in DB
→ return response
```

### Key Design Decisions

* Scraping logic lives in `services.py` (separation of concerns)
* Views remain orchestration-only
* Results are persisted for observability and future polling
* Errors are explicitly captured and stored

### Limitations (Intentional)

* Request blocks until scraping completes
* Not scalable under concurrent load
* No task lifecycle abstraction

### Why This Phase Exists

To **understand the blocking nature of synchronous I/O** before introducing async complexity.

---

## Phase 2 — Async-Ready API & Task Lifecycle

### Goal

Design the API **as if tasks were asynchronous**, without introducing concurrency yet.

### What Happens

```
POST /get_data/
→ create Task (PENDING)
→ perform scraping (still blocking)
→ update Task status (COMPLETED / FAILED)
→ return task ID (202 Accepted)

GET /tasks/<id>/
→ poll task status
```

### Key Improvements

* Introduced `Task` model with lifecycle states:

  * `PENDING`
  * `COMPLETED`
  * `FAILED`
* Client no longer depends on immediate results
* API contract is async-compatible
* Polling endpoint added

### What Is *Not* Async Yet

* Scraping still blocks the Django worker
* No background execution
* No parallelism

### Why This Phase Matters

This phase separates:

* **API design** from
* **execution model**

This is the exact transition point from junior → backend engineer thinking.

---

## What Comes Next (Phase 3)

Move task execution out of the request lifecycle using a background worker (Celery).

---
## Phase 3 – Background Task Processing with Celery

### What Changed
Scraping logic was moved from the Django request lifecycle
to a background Celery task.

Django now enqueues scraping jobs to Redis instead of
executing them synchronously.

### Why This Was Done
- Prevent HTTP request blocking
- Decouple long-running work from web requests
- Introduce event-driven task execution

### Current Behavior
- Celery worker fetches and scrapes the URL
- Scraped data is not saved to the database
- No result backend or retries are configured
- Tasks are fire-and-forget

### What This Phase Does NOT Include
- Database persistence
- Task retries or failure handling
- Returning results to frontend

This phase establishes the minimum viable Celery setup
and task execution flow.

## Phase 4 — Move task execution fully into Celery and observe real failure behavior.

### What changed:

Views now only create a DB task and enqueue it using delay(task_id)

Celery task:

Accepts Task DB ID

Marks task RUNNING

Performs scraping (blocking work)

Updates DB to COMPLETED or FAILED

Introduced:

acks_late=True

retries

simulated long execution (sleep)

Worker crashes were intentionally triggered to observe:

orphaned RUNNING tasks

non-guaranteed requeue behavior on Windows + solo pool

DB state inconsistency vs broker state

### Key learning:
Celery manages message delivery, not business state correctness.
Application must handle recovery of stuck tasks.



---

# Phase 5 - Build self-healing task state using only:

- Django
- DB
- Time

No new Celery config.


# Phase 6 — Task Idempotency and Reconciliation, enforce task correctness with locking, heartbeats, and reconciliation

## Goal
Ensure safe re-running of orphaned or partially executed tasks without Celery tricks or automatic retries. Focus on correctness.

- Added explicit task state machine methods
- Implemented heartbeat-based liveness detection
- Added reconciler for orphaned RUNNING tasks
- Used select_for_update for safe task acquisition
- Added OCC checks to prevent duplicate completion
- Ensured correctness under worker crashes and retries

## Key Changes / Learnings

1. **Idempotency**
   - Tasks can be safely re-run.
   - Achieved by using:
     - `select_for_update()` — locks the DB row for the task during execution.
     - `transaction.atomic()` — ensures all DB updates happen atomically.
   - Prevents race conditions when multiple workers attempt to pick the same task.

2. **Heartbeat**
   - Each task updates `last_heartbeat` periodically.
   - Used to detect orphaned tasks that are stuck in `RUNNING`.

3. **Reconciliation Command**
   - Custom Django management command runs continuously:
     - Queries tasks with `status = RUNNING` and `last_heartbeat < threshold`.
     - Resets them to `PENDING`.
   - Ensures orphaned tasks can be retried safely.

4. **Celery Settings**
   - `acks_late=True` ensures tasks are acknowledged only after completion.
   - `max_retries` and `default_retry_delay` added to handle temporary failures.
   - Redis broker holds task messages; Celery workers consume tasks one at a time.

5. **Task Flow**
    - PENDING → RUNNING → COMPLETED
    - PENDING → RUNNING → FAILED
    - RUNNING → PENDING (via reconciliation)

6. **Race Conditions & Why**
- Without row locking, multiple workers can pick the same task → duplicate work.
- Without transactions, partially completed tasks can leave DB in inconsistent state.
- select_for_update + atomic = safe guard against concurrency issues.

7. **Observation**
- Killing a worker mid-task demonstrates:
  - Tasks may remain `RUNNING` in DB (orphaned).
  - `reconcile_tasks` successfully detects and resets them.I
  - Heartbeat timestamp is critical to detect inactivity.

## Takeaways
- Workers are stateless; DB is source of truth.
- Redis is just a broker for task queuing.
- Reconciliation + idempotency ensures correctness in case of worker crashes.
- select_for_update and atomic transactions are essential to prevent race conditions and ensure safe re-execution.
