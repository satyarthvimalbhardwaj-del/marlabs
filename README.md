# Blog Platform Backend API

## Project Overview

The Blog Platform Backend API is a production-ready REST API built with FastAPI and PostgreSQL, designed to power a modern blogging platform with comprehensive user management, content moderation, and real-time communication features. This backend service implements clean architecture principles with clear separation of concerns across CRUD operations, business logic services, and data transfer objects.

The platform provides a complete blogging solution with JWT-based authentication, role-based access control (RBAC), content approval workflows, and real-time features including Server-Sent Events for notifications and WebSocket support for live comments. The application is fully containerized with Docker, includes structured logging and comprehensive error handling, and is ready for deployment on cloud platforms or traditional infrastructure.

## Key Features

**Authentication and Authorization**
- User registration with email validation and secure password hashing using bcrypt
- JWT token-based authentication with access tokens (30 min) and refresh tokens (7 days)
- Role-based access control supporting three roles: user, admin, and l1_approver
- Secure token validation and automatic refresh mechanisms

**Blog Management**
- Complete CRUD operations for blog articles with markdown content support
- Three-stage approval workflow: users create blogs in pending status, admins/approvers review and approve or reject, only approved blogs are publicly visible
- Author-based filtering, pagination, and search capabilities
- Draft saving and restoration functionality
- Image URL storage and management

**Real-Time Features**
- Server-Sent Events (SSE) for real-time admin notifications when blogs are submitted for approval
- WebSocket support for live comment functionality under blog posts
- Automatic connection management and message broadcasting

**Feature Request System**
- User submission of feature requests with detailed descriptions
- Priority rating system (0-10 scale)
- Admin dashboard for managing requests with status tracking (pending, accepted, declined)

**Security and Production Readiness**
- HTTPS enforcement, CORS configuration, and input validation using Pydantic
- SQL injection prevention through ORM and XSS protection
- Structured JSON logging with rotation and configurable retention
- Database connection pooling and async operations for high performance
- Comprehensive exception handling with custom error classes

## Technology Stack

**Backend Framework:** FastAPI 0.109.0+, Python 3.10+, Uvicorn/Gunicorn ASGI server

**Database:** PostgreSQL 13+ with asyncpg driver, SQLAlchemy 2.0+ async ORM, Alembic migrations

**Authentication:** python-jose for JWT tokens, passlib with bcrypt for password hashing

**Testing:** pytest, pytest-asyncio, httpx, FastAPI TestClient, pytest-cov for coverage

**DevOps:** Docker and Docker Compose, Nginx/Caddy reverse proxy, Redis for session storage

## Architecture

The application follows clean architecture with five distinct layers:

1. **API Layer** - FastAPI routes, request/response handling, dependency injection
2. **Service Layer** - Business logic, validation, transaction orchestration
3. **CRUD Layer** - Database operations, query building, data persistence
4. **Models Layer** - SQLAlchemy ORM models, table relationships, constraints
5. **DTOs/Schemas** - Pydantic models for data validation and serialization

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 13 or higher
- Docker and Docker Compose (optional)
- Git

