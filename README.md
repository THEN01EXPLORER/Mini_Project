# Resume Screener AI | Full Stack Platform

A production-grade Resume Screening & Batch Ranking platform. It uses AI to parse resumes, perform semantic matching against job descriptions, and detect bias.

## Features

- **Batch Resume Ranking:** Upload up to 10 resumes at once and get a ranked leaderboard.
- **Premium Glassmorphic UI:** A beautiful Next.js frontend with animations and dark mode.
- **Gemini AI Extraction:** Structured skill extraction with automatic retries and exponential backoff.
- **Fairness & Bias Detection:** Analyzes the job description and candidate scores for potential biases.
- **Semantic Matching:** Uses local `sentence-transformers` embeddings (no API costs).
- **Authentication:** JWT-based login and registration system.

## Tech Stack

### Backend (FastAPI)
- **FastAPI** - High-performance async Python web framework
- **Google Gemini API** - For intelligent resume text extraction
- **ChromaDB & Sentence-Transformers** - Local vector storage and semantic matching
- **slowapi & tenacity** - Rate limiting and API resilience

### Frontend (Next.js)
- **Next.js 15+** - React framework with App Router
- **Tailwind CSS v4** - Styling and glassmorphic design system
- **TanStack Query** - Async state management and API data fetching

## Setup Instructions

### 1. Backend Setup
```bash
# Clone the repository
git clone <repository-url>
cd Mini_Project

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows Git Bash
# OR: .\venv\Scripts\activate # On Windows CMD/Powershell

# Install dependencies
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY from Google AI Studio

# Start the server
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
Open a **new** terminal window:
```bash
cd frontend-next

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 3. Usage
- **Web UI:** Open [http://localhost:3000](http://localhost:3000)
- **API Docs:** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API Endpoints
- `POST /api/v1/auth/register` - Create an account
- `POST /api/v1/auth/login` - Get JWT token
- `POST /api/v1/screen` - Analyze a single resume
- `POST /api/v1/rank` - Batch rank up to 10 resumes

## License
MIT
