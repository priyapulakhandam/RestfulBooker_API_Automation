# Restful-Booker API Automation Suite

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pytest](https://img.shields.io/badge/Pytest-9.2%2B-orange.svg)](https://docs.pytest.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Clean%20Architecture-brightgreen.svg)]()

Production-grade automated API testing framework developed using **Python**, **Pytest**, **Requests**, and **Pydantic** to validate the [Restful-Booker](https://restful-booker.herokuapp.com) API.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Framework Design](#architecture--framework-design)
3. [Test Coverage](#test-coverage)
   - [Part (a): Happy Path Request Chain](#part-a-happy-path-request-chain)
   - [Part (b): Negative Test Cases](#part-b-negative-test-cases)
4. [Project Structure](#project-structure)
5. [Prerequisites & Installation](#prerequisites--installation)
6. [How to Run the Tests](#how-to-run-the-tests)
   - [Running against the Live Heroku API](#1-running-against-the-live-heroku-api)
   - [Running against the Built-in Mock Server (Offline / Fallback)](#2-running-against-the-built-in-mock-server-offline--fallback)
   - [Running Specific Test Suites](#3-running-specific-test-suites)
7. [Reporting](#reporting)
8. [Video Presentation Walkthrough](#video-presentation-walkthrough)

---

## 🎯 Project Overview

This test suite satisfies all requirements for **Q2. API Automation: Restful-Booker (4 points)**:
- **(a) Happy Path Chain (2 pts)**: End-to-end request chaining from authentication, booking creation, retrieval, authenticated update, to deletion. Dynamic extraction and reuse of `bookingid` and auth `token`.
- **(b) Negative Cases (2 pts)**: Robust negative testing verifying API responses when updating without a token (403 Forbidden), querying a non-existent ID (404 Not Found), and attempting to fetch a deleted booking (404 Not Found).
- **Resilience & Fallback**: Includes a built-in, zero-dependency in-memory mock server mimicking Restful-Booker so tests never fail when the shared Heroku sandbox is down, sleeping, or undergoing periodic database resets.

---

## 🏗️ Architecture & Framework Design

The suite is engineered according to enterprise-grade API test automation design patterns:

- **Layered / Client-Based Architecture**:
  - `core/api_client.py`: Base HTTP engine encapsulating `requests.Session` with structured logging (method, URL, status code, latency).
  - `core/booker_client.py`: High-level domain client modeling Restful-Booker resources (`ping`, `auth`, `booking`).
- **Strict Data Contracts & Schema Validation**:
  - `models/booking.py`: Pydantic V2 models (`BookingPayload`, `CreateBookingResponse`, `BookingResponse`, `AuthResponse`) ensuring runtime response schema validation.
- **Dynamic Test Data Generation**:
  - `utils/data_generator.py`: Generates randomized booking details using `Faker`, preventing payload collisions in shared multi-tenant test environments.
- **Configurability & Environment Isolation**:
  - `config/settings.py`: Centralized configuration managing URLs, timeouts, and credentials with `.env` override capability.
- **Zero-Dependency Mock Server**:
  - `mock_server/local_mock.py`: Built using standard library `http.server` to provide high-speed local testing without third-party server dependencies.

---

## 🧪 Test Coverage

### Part (a): Happy Path Request Chain
`tests/test_happy_path_chain.py`

| Step | Method & Endpoint | Payload / Headers | Expected Status | Key Assertions & Validations |
|---|---|---|---|---|
| **1** | `POST /auth` | `{"username": "admin", "password": "password123"}` | `200 OK` | Schema validation; extracts valid auth `token`. |
| **2** | `POST /booking` | Dynamic booking JSON | `200 OK` | Schema validation; extracts `bookingid > 0`; verifies all fields (`firstname`, `lastname`, `totalprice`, `dates`, `additionalneeds`). |
| **3** | `GET /booking/{id}` | Reuses extracted `bookingid` | `200 OK` | Schema validation; verifies persisted fields match created payload. |
| **4** | `PUT /booking/{id}` | Updated JSON, `Cookie: token={token}` | `200 OK` | Schema validation; verifies all fields updated to new values. |
| **5** | `DELETE /booking/{id}` | `Cookie: token={token}` | `201 Created` | Verifies Restful-Booker deletion status `201` and body text `"Created"`. |
| **6** | `GET /booking/{id}` | Query deleted `bookingid` | `404 Not Found` | Verifies resource is no longer retrievable and body text is `"Not Found"`. |

---

### Part (b): Negative Test Cases
`tests/test_negative_cases.py`

| Case | Scenario | Request Details | Expected Status | Expected Body & Verification |
|---|---|---|---|---|
| **(i)** | **Update booking without token** | `PUT /booking/{id}` with no `Cookie` header or token | `403 Forbidden` | Body text is `"Forbidden"`. Also verifies with forged token (403) and confirms database entity was untouched. |
| **(ii)** | **Fetch non-existent booking ID** | `GET /booking/999999999` | `404 Not Found` | Body text is `"Not Found"`. |
| **(iii)** | **Fetch deleted booking again** | Create -> Delete -> `GET /booking/{id}` | `404 Not Found` | Body text is `"Not Found"`. |
| **Bonus** | **Delete without token** | `DELETE /booking/{id}` without token | `403 Forbidden` | Body text is `"Forbidden"`. Confirms resource remains intact. |
| **Bonus** | **Auth with invalid credentials** | `POST /auth` with bad user/password | `200 OK` | Body contains `{"reason": "Bad credentials"}` and no token. |

---

## 📁 Project Structure

```
RestfulBooker_API_Automation/
├── config/
│   ├── __init__.py
│   └── settings.py          # Central configuration & env management
├── core/
│   ├── __init__.py
│   ├── api_client.py        # Base HTTP client with logging & session handling
│   └── booker_client.py     # Domain-specific Restful-Booker API operations
├── models/
│   ├── __init__.py
│   └── booking.py           # Pydantic models for request/response validation
├── utils/
│   ├── __init__.py
│   ├── data_generator.py    # Dynamic data generation with Faker
│   └── logger.py            # Standardized logger
├── mock_server/
│   ├── __init__.py
│   └── local_mock.py        # In-memory mock server for offline/fallback testing
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures, hooks & teardown safety
│   ├── test_happy_path_chain.py # Part (a) Chained workflow
│   └── test_negative_cases.py   # Part (b) Error & security cases
├── reports/
│   └── report.html          # Self-contained HTML test report
├── .env.example             # Template environment variables
├── .gitignore
├── pytest.ini               # Pytest configuration & live log settings
├── requirements.txt         # Pinned project dependencies
└── README.md                # Documentation & video guide
```

---

## 🚀 Prerequisites & Installation

### 1. Clone or Open the Workspace
```bash
cd /Users/krishnapriya/RestfulBooker_API_Automation
```

### 2. Create and Activate Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚡ How to Run the Tests

### 1. Running against the Live Heroku API
Runs all test cases against the live public instance `https://restful-booker.herokuapp.com`:
```bash
pytest
```
*Verbose output with detailed logs:*
```bash
pytest -v -s
```

### 2. Running against the Built-in Mock Server (Offline / Fallback)
If the public Heroku sandbox is sleeping, unreachable, rate-limited, or undergoing its periodic reset:
```bash
pytest --mock
```
*Or set via environment variable:*
```bash
USE_MOCK=true pytest
```

### 3. Running Specific Test Suites
- **Only Happy Path Chain:**
  ```bash
  pytest tests/test_happy_path_chain.py -v
  ```
- **Only Negative Cases:**
  ```bash
  pytest tests/test_negative_cases.py -v
  ```
- **Filter by Markers:**
  ```bash
  pytest -m chain
  pytest -m negative
  ```

---

## 📊 Reporting

The suite automatically generates a self-contained HTML execution report at:
```
reports/report.html
```
Open it in any browser:
```bash
open reports/report.html
```

---

## 🎥 Video Presentation Walkthrough

When recording your demonstration video, you can follow this structured 3-minute talking track:

1. **Introduction (30s)**:
   - State the problem: Automated testing of the Restful-Booker API covering happy path request chaining and negative edge cases.
   - Mention the tech stack: Python 3, Pytest, Requests, Pydantic, and Pytest-HTML.
   - Mention fallback handling: Note that Heroku is a shared public sandbox that resets periodically, so our framework supports both the live Heroku API and a local mock server via `--mock`.

2. **Code Architecture (45s)**:
   - Highlight clean separation of concerns:
     - `core/booker_client.py` for API interaction encapsulation.
     - `models/booking.py` using Pydantic for schema contracts.
     - `utils/data_generator.py` for dynamic, collision-free test data.
     - `tests/conftest.py` for fixture-based resource lifecycle and safe teardown.

3. **Part (a) Happy Path Chain Walkthrough (45s)**:
   - Show `tests/test_happy_path_chain.py`:
     - Highlight `POST /auth` obtaining token.
     - Highlight `POST /booking` generating and capturing `bookingid`.
     - Highlight request chaining: passing `bookingid` into `GET /booking/{id}`, `PUT /booking/{id}`, and `DELETE /booking/{id}`.
     - Point out strict status code assertions (200, 201 for delete) and deep body field validations.

4. **Part (b) Negative Test Cases Walkthrough (45s)**:
   - Show `tests/test_negative_cases.py`:
     - Case (i): Updating without token asserts `403 Forbidden` and text `"Forbidden"`.
     - Case (ii): Fetching non-existent ID `999999999` asserts `404 Not Found` and text `"Not Found"`.
     - Case (iii): Fetching deleted booking ID asserts `404 Not Found`.

5. **Live Execution (30s)**:
   - Run `pytest -v` in the terminal and show all green passing tests.
   - Run `pytest --mock` to demonstrate seamless fallback execution.
   - Display the generated HTML report in `reports/report.html`.
