# AI Resume Analyzer 🎯

An advanced NLP-powered resume ranking system that intelligently matches resumes against job descriptions using state-of-the-art natural language processing techniques.

## 🌟 Features

### Core Functionality
- **Intelligent Resume Parsing**: Extract text from PDF, DOCX, and TXT resumes
- **Advanced NLP Analysis**: Use spaCy and transformer models for deep semantic understanding
- **Smart Skill Extraction**: Automatically identify technical and soft skills
- **Semantic Matching**: Use sentence transformers for context-aware resume-job matching
- **Multi-Factor Scoring**: Comprehensive ranking based on:
  - Semantic similarity (40%)
  - Skill matching (30%)
  - Experience relevance (20%)
  - Education alignment (10%)

### Technical Features
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Modern Frontend**: React-based UI with drag-and-drop file upload
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based secure authentication
- **File Processing**: Support for PDF, DOCX, and TXT formats
- **Caching**: Redis for performance optimization
- **Logging**: Structured logging with rotation
- **Error Handling**: Comprehensive error handling and validation
- **Testing**: Unit and integration tests with pytest
- **Containerization**: Docker and docker-compose for easy deployment
- **CI/CD**: GitHub Actions pipeline

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ (for local development)
- Node.js 16+ (for frontend development)

### Using Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/UNC-GDSC/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm

# Setup database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

## 📖 Usage

### API Examples

#### Upload and Rank Resumes
```bash
# Upload a job description
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "Looking for an experienced Python developer with FastAPI, NLP, and cloud experience..."
  }'

# Upload resumes
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -F "file=@resume1.pdf" \
  -F "job_id=1"

# Get ranked results
curl "http://localhost:8000/api/v1/jobs/1/rankings"
```

### Web Interface
1. Open http://localhost:3000
2. Create a new job posting
3. Upload multiple resumes (drag & drop supported)
4. View ranked results with detailed breakdowns
5. Export results as CSV or PDF

## 🏗️ Architecture

```
AI-Resume-Analyzer/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration, security
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   ├── nlp/          # NLP processing
│   │   └── utils/        # Utilities
│   ├── tests/            # Test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   └── pages/        # Page components
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🧠 NLP Algorithms

### 1. Resume Parsing
- Text extraction from PDFs using PyPDF2 and pdfplumber
- DOCX parsing with python-docx
- Text cleaning and normalization

### 2. Feature Extraction
- **Skills**: Custom skill database + NLP entity recognition
- **Experience**: Date parsing and calculation
- **Education**: Degree and institution extraction
- **Keywords**: TF-IDF and named entity recognition

### 3. Ranking Algorithm
```python
final_score = (
    0.40 * semantic_similarity +    # BERT embeddings cosine similarity
    0.30 * skill_match_score +      # Jaccard similarity of skills
    0.20 * experience_score +       # Years and relevance
    0.10 * education_score          # Degree level matching
)
```

### 4. Models Used
- **sentence-transformers/all-MiniLM-L6-v2**: Semantic embeddings
- **spaCy en_core_web_sm**: NER and text processing
- **scikit-learn**: TF-IDF and similarity metrics

## 🔒 Security

- JWT authentication with refresh tokens
- Password hashing with bcrypt
- Rate limiting on API endpoints
- File upload validation and scanning
- CORS configuration
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection
- Secure headers (helmet.js)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test
```

## 📊 Performance

- Handles 100+ resumes per job posting
- Average processing time: 2-3 seconds per resume
- API response time: < 100ms (cached)
- Supports concurrent requests with async processing

## 🛠️ Configuration

Key environment variables:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/resumedb

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,docx,txt

# NLP Models
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm
```

## 📈 Future Enhancements

- [ ] Support for more file formats (RTF, ODT)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Email notifications
- [ ] Batch processing API
- [ ] Integration with ATS systems
- [ ] Custom scoring weights
- [ ] AI-powered interview question generation

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📝 License

MIT License - see LICENSE file for details

## 👥 Authors

Built with ❤️ by UNC GDSC

## 📧 Support

For issues and questions, please create a GitHub issue or contact us at support@example.com
