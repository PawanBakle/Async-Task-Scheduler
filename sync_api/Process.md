

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

# 🔖 Commit Messages

### Phase 1 Commit

```
feat: add synchronous scraping with service layer and persistence
```

### Phase 2 Commit

```
feat: introduce task lifecycle and async-ready polling API
```

---

