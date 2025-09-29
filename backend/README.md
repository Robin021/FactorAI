# TradingAgents Backend

FastAPI backend for the TradingAgents stock analysis platform.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Update environment variables in `.env` file

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest
```

## Project Structure

```
backend/
├── app/                 # Main application
├── api/                 # API routes
├── core/                # Core functionality
├── services/            # Business logic
├── models/              # Data models
├── utils/               # Utilities
├── requirements.txt     # Dependencies
└── pyproject.toml       # Project configuration
```