# PoseDetect Server Setup Guide

This guide covers setting up the FastAPI backend server for PoseDetect using modern Python tooling with `uv`.

## 📋 Prerequisites

- **Python 3.8+** (3.11+ recommended for best performance)
- **uv** - Fast Python package installer (replaces pip)
- **Git** (for cloning and version control)

## 🚀 Installing uv

### Option 1: Using the installer script (Recommended)
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Option 2: Using package managers
```bash
# Using Homebrew (macOS)
brew install uv

# Using Cargo (Rust)
cargo install uv

# Using pip (fallback)
pip install uv
```

### Verify Installation
```bash
uv --version
```

## 🏗️ Project Setup

### 1. Navigate to Server Directory
```bash
cd server
```

### 2. Create Virtual Environment & Install Dependencies
```bash
# Create and activate virtual environment with all dependencies
uv sync

# Or if you want development dependencies included
uv sync --extra dev

# For all optional dependencies (dev, lint, docs)
uv sync --extra all
```

### 3. Activate Virtual Environment
```bash
# The virtual environment is automatically created in .venv/
# Activate it manually if needed:

# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

### 4. Environment Configuration
Create a `.env` file in the server directory:
```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

Example `.env` configuration:
```env
# API Configuration
DEBUG=true
HOST=127.0.0.1
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./posedetect.db

# File Storage
MAX_FILE_SIZE=524288000  # 500MB
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
TEMP_DIR=./temp

# Security
SECRET_KEY=your-secret-key-change-in-production

# Processing
MAX_CONCURRENT_JOBS=2
VIDEO2POSE_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
```

### 5. Initialize Database
```bash
# Run database migrations
uv run alembic upgrade head

# Or start the server (it will auto-create tables)
uv run python main.py
```

## 🚀 Running the Server

### Development Server
```bash
# Start with hot reload
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Or using the main script
uv run python main.py
```

### Production Server
```bash
# Start with optimized settings
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The server will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Development Workflow

### Installing New Dependencies

#### Production Dependencies
```bash
# Add a new dependency
uv add fastapi-users

# Add with version constraint
uv add "sqlalchemy>=2.0.0"

# Add with specific index
uv add --index-url https://pypi.org/simple/ some-package
```

#### Development Dependencies
```bash
# Add development dependency
uv add --dev pytest-xdist

# Add linting tool
uv add --dev ruff
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_api.py

# Run with markers
uv run pytest -m "not slow"
```

### Code Quality Tools

#### Formatting
```bash
# Format code with Black
uv run black .

# Sort imports with isort
uv run isort .

# Format with Ruff (modern alternative)
uv run ruff format .
```

#### Linting
```bash
# Lint with Ruff
uv run ruff check .

# Lint with flake8
uv run flake8 app/

# Type checking with MyPy
uv run mypy app/
```

#### All-in-one Quality Check
```bash
# Run formatting, linting, and tests
uv run ruff format . && uv run ruff check . && uv run pytest
```

### Database Migrations

#### Using Alembic
```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Add new table"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Show migration history
uv run alembic history
```

## 📦 Dependency Management

### Viewing Dependencies
```bash
# Show dependency tree
uv tree

# List installed packages
uv pip list

# Show outdated packages
uv pip list --outdated
```

### Updating Dependencies
```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv add "fastapi>=0.105.0"

# Lock dependencies (creates uv.lock)
uv lock
```

### Removing Dependencies
```bash
# Remove a dependency
uv remove package-name

# Remove development dependency
uv remove --dev package-name
```

## 🔧 Configuration Management

### Environment Variables
The application uses `pydantic-settings` for configuration management. Settings can be configured via:

1. **Environment variables**
2. **`.env` file**
3. **Command line arguments**
4. **Default values in code**

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable debug mode |
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite+aiosqlite:///./posedetect.db` | Database connection string |
| `MAX_FILE_SIZE` | `524288000` | Maximum upload file size (bytes) |
| `MAX_CONCURRENT_JOBS` | `2` | Maximum concurrent processing jobs |
| `LOG_LEVEL` | `INFO` | Logging level |

## 🐳 Docker Support (Optional)

### Build Docker Image
```bash
# Build image
docker build -t posedetect-server .

# Run container
docker run -p 8000:8000 -v $(pwd):/app posedetect-server
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/posedetect
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: posedetect
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🚨 Troubleshooting

### Common Issues

#### 1. uv not found
```bash
# Ensure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Permission errors on Windows
```bash
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. Python version issues
```bash
# Use specific Python version
uv python install 3.11
uv sync --python 3.11
```

#### 4. Database connection errors
```bash
# Check database file permissions
ls -la posedetect.db

# Recreate database
rm posedetect.db
uv run alembic upgrade head
```

#### 5. Package conflicts
```bash
# Clear cache and reinstall
uv cache clean
rm -rf .venv
uv sync
```

### Performance Tips

1. **Use Python 3.11+** for best performance
2. **Enable uvloop** in production (included in uvicorn[standard])
3. **Use multiple workers** for production deployment
4. **Configure proper database pooling** for high load
5. **Use Redis for session storage** in production

### Development Best Practices

1. **Always use virtual environments**
2. **Pin dependency versions** in production
3. **Run tests before commits**
4. **Use type hints** throughout the codebase
5. **Follow PEP 8** style guidelines
6. **Write comprehensive docstrings**
7. **Use async/await** for I/O operations

## 📚 Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic Settings](https://pydantic-docs.helpmanual.io/usage/settings/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install dev dependencies: `uv sync --extra dev`
4. Make changes and add tests
5. Run quality checks: `uv run ruff format . && uv run ruff check . && uv run pytest`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 