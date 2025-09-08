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
	uvicorn $(APP_MODULE) --reload --host 127.0.0.1 --port $(PORT)'

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
