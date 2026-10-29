# SSRF Demonstration Lab

This laboratory demonstrates **Server-Side Request Forgery (SSRF)** vulnerabilities, practical exploitation against internal infrastructure, and defensive countermeasures.

---

## Architecture Overview

The lab spins up three isolated services within an isolated Docker bridge network (`lab-network`):

```
                   [ Attacker / Client ]
                             │
            ┌────────────────┴────────────────┐
     Port 5001 (Vulnerable)            Port 5002 (Secured)
            ▼                                 ▼
   ┌──────────────────┐              ┌──────────────────┐
   │  vulnerable-app  │              │   secured-app    │
   └────────┬─────────┘              └────────┬─────────┘
            │                                 │
            │ (Allowed / Unrestricted)        │ (Blocked by IP filter)
            ▼                                 ✕
   ┌────────────────────────────────────────────────────┐
   │             internal-service:8080                  │
   │           (Restricted Admin API)                   │
   └────────────────────────────────────────────────────┘
```

| Service | Host Port | Network Access | Description |
| :--- | :--- | :--- | :--- |
| **`internal-service`** | *None* (Internal only) | `lab-network` | Private administrative service (simulating internal metadata, databases, or admin APIs). |
| **`vulnerable-app`** | `5001` | `lab-network` | Webhook/fetch proxy vulnerable to SSRF. |
| **`secured-app`** | `5002` | `lab-network` | Webhook/fetch proxy implementing defense-in-depth mitigations. |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose installed

### Launching the Lab
```bash
docker compose up --build
```

To stop the lab:
```bash
docker compose down
```

---

## Exploitation Walkthrough

### 1. Verify Direct Access to Internal Service is Blocked
The internal service is not mapped to any host ports. An external attacker cannot reach it directly:
```bash
curl http://localhost:8080
# Output: Failed to connect to localhost port 8080: Connection refused
```

### 2. SSRF via the Vulnerable Application (Port 5001)
The vulnerable application exposes a `/fetch?url=<target>` endpoint that blindly passes the requested URL to Python's `requests.get()` without scheme, hostname, or IP validation.

Fetch a legitimate external target:
```bash
curl "http://localhost:5001/fetch?url=http://example.com"
```

Pivot into the private internal network using Docker's internal DNS:
```bash
curl "http://localhost:5001/fetch?url=http://internal-service:8080"
```
**Response:**
```text
Internal Admin API - Restricted Access Only
```
> **Result**: The vulnerable proxy was abused to reach an internal network resource that is completely inaccessible from the outside.

---

## Defensive Mitigation (Port 5002)

The `secured-app` introduces several defense-in-depth layers to eliminate SSRF:

1. **Protocol / Scheme Whitelisting**:
   - Only `http` and `https` schemes are accepted. Protocols like `file://`, `gopher://`, `dict://`, or `ftp://` are rejected immediately.
2. **DNS Resolution & Private IP Space Filtering**:
   - Resolves the hostname via `socket.getaddrinfo()` before dispatching the request.
   - Rejects any destination address falling within private (`RFC 1918`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), multicast, or reserved IP ranges using Python's `ipaddress` library.
3. **Disabled Redirect Following**:
   - Sets `allow_redirects=False` on the HTTP client to prevent open-redirect bypasses (where a permitted public URL redirects back into private IP spaces).

### Testing the Mitigations

Attempting to reach the internal service via the secured proxy:
```bash
curl -i "http://localhost:5002/fetch?url=http://internal-service:8080"
```
**Response:**
```http
HTTP/1.1 403 FORBIDDEN
Content-Type: text/html; charset=utf-8

Request blocked: Target resolves to an internal or restricted network address.
```

Attempting to target localhost/loopback addresses:
```bash
curl -i "http://localhost:5002/fetch?url=http://127.0.0.1:5000"
```
**Response:**
```http
HTTP/1.1 403 FORBIDDEN
Content-Type: text/html; charset=utf-8

Request blocked: Target resolves to an internal or restricted network address.
```

Legitimate public requests continue to work normally:
```bash
curl "http://localhost:5002/fetch?url=http://example.com"
```

---

## Directory Structure

```
.
├── docker-compose.yml       # Multi-container lab orchestration
├── internal-service/
│   ├── app.py               # Simulated restricted internal API (Port 8080)
│   └── Dockerfile
├── vulnerable/
│   ├── app.py               # Vulnerable fetch endpoint (Port 5000 -> 5001)
│   └── Dockerfile
└── secured/
    ├── app.py               # Hardened fetch endpoint with IP validation (Port 5000 -> 5002)
    └── Dockerfile
```

