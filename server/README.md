# PoseDetect Server

A high-performance, async FastAPI backend server for the PoseDetect AI video analysis system. Built with modern Python practices using `uv` for dependency management.

## 🚀 Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to server directory
cd server

# Install dependencies and create virtual environment
uv sync

# Start development server
uv run python main.py
```

The server will be available at http://localhost:8000 with interactive API docs at http://localhost:8000/docs.

## 📋 Features

### Core Functionality
- **File Upload & Management**: Multi-format support with drag-and-drop and URL uploads
- **Async Processing**: Background job processing with real-time status updates
- **CLI Integration**: Robust integration with existing `video2pose.py` command-line tool
- **RESTful API**: Clean, well-documented API endpoints following OpenAPI standards

### Technical Features
- **High Performance**: Async/await throughout with uvicorn ASGI server
- **Type Safety**: Full type annotations with Pydantic validation
- **Database Agnostic**: SQLAlchemy async ORM supporting SQLite, PostgreSQL, MySQL
- **Background Tasks**: Efficient job queue system for video processing
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Configuration**: Environment-based configuration with sensible defaults
- **Logging**: Structured logging with configurable levels
- **Testing**: Comprehensive test suite with pytest and async support

## 🏗️ Architecture

```
server/
├── app/                         # Main application package
│   ├── api/                     # API routes and endpoints
│   │   └── v1/                  # API version 1
│   │       ├── endpoints/       # Route handlers
│   │       └── router.py        # Main API router
│   ├── core/                    # Core application components
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database setup and session management
│   │   ├── background_tasks.py  # Background job processing
│   │   └── logging_config.py   # Logging configuration
│   ├── models/                  # SQLAlchemy database models
│   │   ├── file.py             # File model
│   │   └── processing_job.py   # Processing job model
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── file.py             # File-related schemas
│   │   └── processing.py       # Processing-related schemas
│   └── services/                # Business logic layer
│       ├── file_service.py     # File operations service
│       └── processing_service.py # Processing operations service
├── tests/                       # Test suite
├── migrations/                  # Database migrations (Alembic)
├── main.py                     # Application entry point
├── pyproject.toml              # Modern Python project configuration
├── SETUP.md                    # Detailed setup instructions
└── README.md                   # This file
```

## 🔧 API Endpoints

### File Management
- `POST /api/v1/files/upload` - Upload file for processing
- `POST /api/v1/files/upload-url` - Upload file from URL
- `GET /api/v1/files/` - List uploaded files
- `GET /api/v1/files/{id}` - Get file details
- `PATCH /api/v1/files/{id}` - Update file details
- `DELETE /api/v1/files/{id}` - Delete file
- `GET /api/v1/files/{id}/download` - Download original file
- `GET /api/v1/files/{id}/metadata` - Get file metadata

### Processing Management
- `POST /api/v1/processing/start` - Start processing job
- `GET /api/v1/processing/jobs` - List processing jobs
- `GET /api/v1/processing/jobs/{id}` - Get job details
- `POST /api/v1/processing/jobs/{id}/cancel` - Cancel processing job
- `GET /api/v1/processing/jobs/{id}/download` - Download processing results

### Statistics
- `GET /api/v1/stats` - Get system statistics
- `GET /health` - Health check endpoint

## 🛠️ Development

### Prerequisites
- Python 3.8+ (3.11+ recommended)
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Setup Development Environment

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd server
   uv sync --extra dev
   ```

2. **Environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize database**:
   ```bash
   uv run alembic upgrade head
   ```

4. **Start development server**:
   ```bash
   uv run python main.py
   ```

### Development Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Format code
uv run black .
uv run isort .

# Lint code
uv run ruff check .
uv run mypy app/

# Create database migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head
```

## 🔧 Configuration

The application uses environment variables for configuration. Key settings include:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable debug mode |
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite+aiosqlite:///./posedetect.db` | Database URL |
| `MAX_FILE_SIZE` | `524288000` | Max upload size (500MB) |
| `MAX_CONCURRENT_JOBS` | `2` | Max processing jobs |
| `VIDEO2POSE_SCRIPT` | `../src/video2pose.py` | Path to CLI script |
| `LOG_LEVEL` | `INFO` | Logging level |

See `.env.example` for complete configuration options.

## 🚀 Deployment

### Production Setup

1. **Install dependencies**:
   ```bash
   uv sync --no-dev
   ```

2. **Set production environment**:
   ```bash
   export DEBUG=false
   export SECRET_KEY="your-secure-secret-key"
   export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/posedetect"
   ```

3. **Run with multiple workers**:
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Deployment

```bash
# Build image
docker build -t posedetect-server .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  -e SECRET_KEY="your-secret-key" \
  -v $(pwd)/uploads:/app/uploads \
  posedetect-server
```

### Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Configure proper logging
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS/TLS
- [ ] Configure monitoring
- [ ] Set up backups
- [ ] Use environment variables for secrets
- [ ] Configure CORS properly

## 🧪 Testing

The project includes comprehensive tests covering:

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: Model and repository testing
- **Performance Tests**: Load and stress testing

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m "unit"
uv run pytest -m "integration"

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run performance tests
uv run pytest -m "slow"
```

## 📊 Monitoring & Observability

### Health Checks
- `/health` - Basic health check
- Database connectivity check
- Background task status
- Disk space monitoring

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking with stack traces
- Performance metrics

### Metrics (Optional)
- Request count and latency
- Database query metrics
- Background job metrics
- System resource usage

## 🔒 Security

### Built-in Security Features
- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- File type validation
- File size limits
- Error message sanitization

### Security Best Practices
- Use HTTPS in production
- Validate all file uploads
- Sanitize file names
- Implement rate limiting
- Use secure headers
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install dev dependencies: `uv sync --extra dev`
4. Make your changes
5. Add tests for new functionality
6. Run the test suite: `uv run pytest`
7. Run code quality checks: `uv run ruff check . && uv run black . && uv run mypy app/`
8. Commit your changes: `git commit -m 'Add amazing feature'`
9. Push to the branch: `git push origin feature/amazing-feature`
10. Open a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive docstrings
- Add tests for new functionality
- Keep functions small and focused
- Use async/await for I/O operations

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and setup instructions
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when server is running)
- **[Database Schema](docs/database.md)** - Database design and relationships
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Database errors**: Check database URL and permissions
3. **File upload failures**: Verify file size and type restrictions
4. **Processing timeouts**: Adjust `VIDEO2POSE_TIMEOUT` setting

### Debug Mode
Enable debug mode for detailed error information:
```bash
export DEBUG=true
uv run python main.py
```

### Logs
Check application logs for detailed error information:
```bash
tail -f logs/posedetect.log
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🔗 Related Projects

- [PoseDetect Frontend](../frontend/README.md) - React/Next.js web interface
- [PoseDetect Core](../README.md) - Main project documentation
- [Video2Pose CLI](../src/video2pose.py) - Core pose detection algorithm 