.PHONY: help install dev build up down clean test lint

help:
	@echo "AI Resume Analyzer - Development Commands"
	@echo ""
	@echo "make install       - Install dependencies for backend and frontend"
	@echo "make dev          - Run development servers (backend and frontend)"
	@echo "make build        - Build Docker images"
	@echo "make up           - Start all services with Docker Compose"
	@echo "make down         - Stop all services"
	@echo "make clean        - Clean up containers, volumes, and build artifacts"
	@echo "make test         - Run tests for backend and frontend"
	@echo "make lint         - Run linters"
	@echo "make logs         - Show logs from all services"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	cd backend && python -m spacy download en_core_web_sm
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm start

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	@echo "Stopping all services..."
	docker-compose down

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	rm -rf frontend/node_modules
	rm -rf frontend/build
	@echo "Cleanup complete!"

test:
	@echo "Running backend tests..."
	cd backend && pytest --cov=app tests/
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

lint:
	@echo "Linting backend..."
	cd backend && flake8 app
	@echo "Linting frontend..."
	cd frontend && npm run lint || echo "No lint script configured"

logs:
	docker-compose logs -f

restart:
	@make down
	@make up

init-db:
	@echo "Initializing database..."
	docker-compose exec backend python -c "from app.database import init_db; init_db()"
	@echo "Database initialized!"
