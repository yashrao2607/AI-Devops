# Payment Checkout Service

A lightweight financial checkout microservice.

## Architecture & Production Deployment Requirements
- The application processes customer checkouts and orders.
- **Mandatory Requirement:** Production deployment requires REDIS_URL for distributed transaction caching and rate limiting.
- Services must read all database endpoints dynamically from environment variables.

## Running Tests
Run automated test suite:
```bash
pytest tests/ -v
```
