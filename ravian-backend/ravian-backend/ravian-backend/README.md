# Ravian Backend API

Comprehensive backend API for Ravian - AI-powered lead generation and management platform.

## Features

- FastAPI with automatic OpenAPI documentation
- Multi-tenant architecture ready
- JWT authentication support
- Redis integration for caching and sessions
- PostgreSQL database support
- Celery for async task processing
- Health check endpoints
- API versioning (/api/v1)
- Rate limiting ready
- CORS support

## Project Structure

```
ravian-backend/
├── app/
│   ├── routers/           # API route modules
│   │   ├── v1/           # Version 1 API endpoints
│   │   └── health.py     # Health check endpoints
│   ├── middleware/        # Middleware modules
│   ├── core/             # Core configuration
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
└── .env                 # Environment configuration
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`

3. Run the application:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status

### API v1 Endpoints
- `GET/POST /api/v1/chatbot` - Chatbot operations
- `GET/POST /api/v1/leads` - Lead management
- `GET/POST /api/v1/calls` - Call management
- `GET/POST /api/v1/demos` - Demo scheduling
- `GET/POST /api/v1/analytics` - Analytics data
- `GET/POST /api/v1/teaching` - Teaching/training
- `GET/POST /api/v1/context` - Context management

## Documentation

- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

## Development

The application includes:
- Automatic reload in development mode
- Comprehensive error handling
- Structured logging (via print statements)
- Environment-based configuration
- CORS middleware for web clients

## Next Steps

1. Implement JWT authentication middleware
2. Add rate limiting per tenant
3. Set up database models and migrations
4. Configure Redis connections
5. Implement Celery tasks
6. Add comprehensive error handling
7. Set up Docker containers
8. Add unit tests

## License

Private - Ravian Platform