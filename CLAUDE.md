# Linux Server Manager

## Project Overview

Linux Server Manager is a self-hosted web application for monitoring
and administering Linux servers from a centralized dashboard.

The project is designed to be:

- Open source
- Self-hosted
- Lightweight
- Secure
- Modular
- Docker-compatible
- Easy to deploy
- Easy to maintain

The primary target is Linux servers used in homelabs,
development environments and small infrastructures.

---

# Goals

The application should provide:

1. System monitoring
2. Process monitoring
3. Service management
4. Storage monitoring
5. Network monitoring
6. Log viewing
7. Docker monitoring
8. User management
9. SSH information
10. System information

The application must prioritize security and reliability
over adding features quickly.

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite

## Frontend

- React
- TypeScript
- Tailwind CSS

## Infrastructure

- Docker
- Docker Compose

## Testing

- pytest
- Playwright

## CI/CD

- GitHub Actions

---

# Architecture

The application follows a client-server architecture.

```
Frontend
    ↓
REST API
    ↓
FastAPI
    ↓
Service layer
    ↓
System interfaces
```

The frontend must never directly execute system commands.

All privileged operations must go through
a controlled backend service.

---

# Security Rules

Security is a first-class requirement.

Never:

- execute arbitrary user input through shell commands
- use `shell=True` unless absolutely necessary
- expose system credentials
- store passwords in plaintext
- commit `.env` files
- expose unrestricted command execution
- trust frontend validation alone

System commands must use safe argument handling.

Example:

GOOD:

```python
subprocess.run(
    ["systemctl", "status", service_name],
    check=True
)
```

BAD:

```python
subprocess.run(
    f"systemctl status {service_name}",
    shell=True
)
```

All user-controlled input must be validated.

---

# Development Rules

Before implementing a feature:

1. Understand the existing architecture.
2. Search the repository for related functionality.
3. Avoid unnecessary refactoring.
4. Implement the smallest maintainable solution.
5. Add tests.
6. Update documentation when necessary.

Do not introduce a new dependency unless there is
a clear technical reason.

Prefer simple solutions over unnecessary abstraction.

---

# Testing

Every significant backend feature must include tests.

Tests should cover:

- normal behaviour
- invalid input
- error conditions
- permission failures
- edge cases

The project should maintain a high level of test coverage.

Never remove tests simply because they are inconvenient.

---

# Git Rules

Use conventional commits.

Examples:

```
feat: add system information endpoint
fix: handle unavailable docker daemon
refactor: simplify metrics service
test: add storage service tests
docs: update installation guide
```

Do not create meaningless commits such as:

- "update"
- "stuff"
- "changes"
- "fixed things"

---

# Code Quality

Code should be:

- readable
- typed where practical
- modular
- documented when necessary
- testable
- maintainable

Avoid:

- duplicated logic
- giant functions
- unnecessary global state
- premature abstractions
- magic numbers
- dead code

---

# Current Development Phase

The project is currently in Phase 1.

Phase 1:

- project structure
- backend foundation
- frontend foundation
- system information
- CPU monitoring
- RAM monitoring
- storage monitoring
- basic dashboard

Do not implement future phases unless explicitly requested.

---

# Definition of Done

A feature is considered complete only when:

- implementation works
- tests exist
- tests pass
- errors are handled
- security implications have been considered
- documentation is updated when necessary
- code follows the project architecture

---

# Claude Code Behaviour

When working on this project:

1. Inspect the repository before modifying files.
2. Explain the intended approach before large changes.
3. Do not rewrite working code without a reason.
4. Do not introduce unnecessary dependencies.
5. Do not disable tests to make them pass.
6. Do not hide errors.
7. Prefer incremental changes.
8. Run relevant tests after modifications.
9. Report what was changed.
10. Report any remaining issues or technical debt.

If requirements are ambiguous, identify the ambiguity
before making a potentially destructive architectural decision.
