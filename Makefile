# ----------------------
# Variables
# ----------------------
APP_MODULE = app.main:app
PORT = 8000
VENV_DIR = venv
ENV_FILE_DEV = .env.development
ENV_FILE_PROD = .env.production

# Detect platform and set venv activation script
ifeq ($(OS),Windows_NT)
    ACTIVATE = $(VENV_DIR)/Scripts/activate
else
    ACTIVATE = $(VENV_DIR)/bin/activate
endif

# ----------------------
# Targets
# ----------------------

# Create virtual env
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		python -m venv $(VENV_DIR); \
	else \
		echo "Virtual environment already exists."; \
	fi

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	source $(ACTIVATE) && pip install -r requirements.txt

# Run development server
dev: venv
	@echo "Running FastAPI in development mode..."
	bash -c 'ENV=development DOTENV_FILE=$(ENV_FILE_DEV) source $(ACTIVATE) && \
	uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port $(PORT)'

# Run production server
prod: venv
	@echo "Running FastAPI in production mode..."
	ENV=production DOTENV_FILE=$(ENV_FILE_PROD) source $(ACTIVATE) && \
	uvicorn $(APP_MODULE) --host 0.0.0.0 --port $(PORT)

# Clean Python cache
clean:
	@echo "Cleaning Python cache..."
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete

# Show help
help:
	@echo "Makefile commands:"
	@echo "  make dev      # Run FastAPI in development mode"
	@echo "  make prod     # Run FastAPI in production mode"
	@echo "  make install  # Install dependencies"
	@echo "  make venv     # Create virtual environment"
	@echo "  make clean    # Clean Python cache"
	@echo "  make help     # Show this help"

# ----------------------
# Docker Targets
# ----------------------

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker-compose build

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker-compose up -d

# Stop Docker container
docker-down:
	@echo "Stopping Docker container..."
	docker-compose down

# View Docker logs
docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f

# Show Docker help
docker-help:
	@echo "Docker commands:"
	@echo "  make docker-build   # Build Docker image"
	@echo "  make docker-run     # Run Docker container"
	@echo "  make docker-down    # Stop Docker container"
	@echo "  make docker-logs    # View Docker logs"
