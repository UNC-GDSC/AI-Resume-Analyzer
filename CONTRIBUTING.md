# Contributing to AI Resume Analyzer

Thank you for your interest in contributing to AI Resume Analyzer! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker and Docker Compose
- PostgreSQL (for local development without Docker)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/UNC-GDSC/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run development server
uvicorn app.main:app --reload
```

3. **Frontend Setup**
```bash
cd frontend
npm install

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run development server
npm start
```

4. **Using Docker**
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Code Style

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Document functions with docstrings
- Maximum line length: 100 characters
- Run `black` for formatting: `black app/`
- Run `flake8` for linting: `flake8 app/`

### JavaScript/React (Frontend)
- Use ES6+ features
- Follow React best practices
- Use functional components with hooks
- Use meaningful variable and function names
- Format with Prettier (if configured)

## Testing

### Backend Tests
```bash
cd backend
pytest --cov=app tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality

4. **Run tests** to ensure everything passes
```bash
make test
```

5. **Commit your changes** with clear, descriptive messages
```bash
git commit -m "Add feature: description of your changes"
```

6. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

7. **Create a Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots (if UI changes)
   - Test results

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests when relevant

Examples:
```
Add resume parsing for PDF files
Fix ranking algorithm edge case
Update documentation for API endpoints
Refactor skill extraction logic
```

## Feature Requests and Bug Reports

### Bug Reports
Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment (OS, Python version, etc.)

### Feature Requests
Include:
- Description of the feature
- Use case and benefits
- Proposed implementation (optional)
- Mockups or examples (if applicable)

## Project Structure

```
AI-Resume-Analyzer/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration, security
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   ├── nlp/          # NLP processing
│   │   └── schemas/      # Pydantic schemas
│   └── tests/            # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── context/      # React context
│   │   └── services/     # API services
│   └── public/           # Static files
└── docs/                 # Documentation
```

## Areas for Contribution

We welcome contributions in these areas:

1. **NLP Improvements**
   - Better skill extraction
   - Multi-language support
   - More accurate parsing algorithms

2. **Features**
   - Batch processing
   - Email notifications
   - Analytics dashboard
   - Export to various formats
   - ATS integrations

3. **UI/UX**
   - Mobile responsiveness
   - Accessibility improvements
   - New themes
   - Better visualizations

4. **Performance**
   - Caching optimizations
   - Database query optimization
   - Frontend performance

5. **Documentation**
   - API documentation
   - User guides
   - Code examples
   - Video tutorials

## Questions?

Feel free to:
- Open an issue for questions
- Join our community discussions
- Contact the maintainers

Thank you for contributing! 🎉
