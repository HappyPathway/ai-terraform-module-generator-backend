# AI Terraform Module Generator Backend

FastAPI backend service for the AI Terraform Module Generator, providing AI-powered module generation and Terraform Registry Protocol implementation.

## Features

- AI-powered Terraform module generation
- Complete Terraform Registry Protocol implementation
- Module validation and testing
- GitHub repository integration
- Version management system
- Role-based access control
- API documentation with OpenAPI/Swagger

## Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Docker and Docker Compose
- OpenAI API key or Claude API key

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/HappyPathway/ai-terraform-module-generator-backend.git
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start services:
```bash
docker compose up -d
```

4. Access API documentation at http://localhost:8000/docs

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key
- `CLAUDE_API_KEY`: Claude API key (if using Claude)
- `JWT_SECRET_KEY`: Secret for JWT token generation
- `GITHUB_TOKEN`: GitHub API token
- `REDIS_URL`: Redis connection string

## Development

### Local Development Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start development server:
```bash
uvicorn app.main:app --reload
```

### Testing

```bash
pytest
```

## Project Structure

```
├── app/                # Application package
│   ├── __init__.py
│   ├── main.py        # FastAPI application
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality
│   ├── models/        # Database models
│   └── services/      # Business logic
├── tests/             # Test suite
├── alembic/           # Database migrations
└── docker/            # Docker configuration
```

## API Documentation

The backend implements these key endpoints:

- `/v1/modules/*`: Terraform Registry Protocol endpoints
- `/api/generate`: Module generation endpoint
- `/api/validate`: Module validation endpoint
- `/auth/*`: Authentication endpoints

Full API documentation is available at `/docs` when running the server.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Related Repositories

- [Main Project](https://github.com/HappyPathway/ai-terraform-module-generator)
- [Frontend Service](https://github.com/HappyPathway/ai-terraform-module-generator-frontend)
- [Infrastructure](https://github.com/HappyPathway/ai-terraform-module-generator-infrastructure)

## License

MIT License - see [LICENSE](LICENSE) for details