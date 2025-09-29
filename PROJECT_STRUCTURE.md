# TradingAgents Project Structure

This document describes the new project structure after the framework migration from Streamlit to FastAPI + React.

## Overview

The project is now organized as a modern web application with separate backend and frontend components:

- **Backend**: FastAPI-based REST API server
- **Frontend**: React + TypeScript single-page application
- **Database**: MongoDB for data persistence, Redis for caching
- **Development**: Docker-based development environment

## Directory Structure

```
TradingAgents-CN/
├── backend/                     # FastAPI backend
│   ├── app/                     # Main application
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI app entry point
│   ├── api/                     # API routes
│   │   └── v1/                  # API version 1
│   ├── core/                    # Core functionality
│   ├── services/                # Business logic services
│   ├── models/                  # Data models
│   ├── utils/                   # Utility functions
│   ├── requirements.txt         # Python dependencies
│   ├── pyproject.toml          # Project configuration
│   ├── .env.example            # Environment variables template
│   ├── Dockerfile.dev          # Development Docker image
│   └── README.md               # Backend documentation
│
├── frontend/                    # React frontend
│   ├── src/                     # Source code
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client services
│   │   ├── stores/             # State management (Zustand)
│   │   ├── types/              # TypeScript type definitions
│   │   ├── utils/              # Utility functions
│   │   ├── hooks/              # Custom React hooks
│   │   ├── test/               # Test utilities
│   │   ├── App.tsx             # Main app component
│   │   └── main.tsx            # Entry point
│   ├── package.json            # Node.js dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   ├── vite.config.ts          # Vite build configuration
│   ├── Dockerfile.dev          # Development Docker image
│   └── README.md               # Frontend documentation
│
├── scripts/                     # Development and deployment scripts
│   ├── dev-setup.sh            # Development environment setup (Unix)
│   ├── dev-setup.ps1           # Development environment setup (Windows)
│   └── mongo-init.js           # MongoDB initialization script
│
├── docker-compose.dev.yml       # Development environment services
├── Makefile                     # Development commands
├── .gitignore                   # Git ignore rules
└── PROJECT_STRUCTURE.md         # This file
```

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **Motor**: Async MongoDB driver
- **Redis**: Caching and session storage
- **Python-JOSE**: JWT token handling
- **Passlib**: Password hashing
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI library with hooks and concurrent features
- **TypeScript**: Static type checking
- **Vite**: Fast build tool and dev server
- **Ant Design**: Enterprise-class UI components
- **Zustand**: Lightweight state management
- **Axios**: HTTP client
- **ECharts**: Data visualization
- **React Router**: Client-side routing

### Development Tools
- **Docker**: Containerization
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **Jest/Vitest**: Testing frameworks
- **Black**: Python code formatting

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start

1. **Set up development environment:**
   ```bash
   # Unix/Linux/macOS
   ./scripts/dev-setup.sh
   
   # Windows
   .\scripts\dev-setup.ps1
   
   # Or use Make
   make setup
   ```

2. **Start all services with Docker:**
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Or start services individually:**
   ```bash
   # Backend (in backend/ directory)
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   
   # Frontend (in frontend/ directory)
   npm install
   npm run dev
   ```

### Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: mongodb://localhost:27017
- **Redis**: redis://localhost:6379

## Development Workflow

### Backend Development
1. Make changes to Python files in `backend/`
2. FastAPI auto-reloads on file changes
3. API documentation updates automatically
4. Run tests: `cd backend && pytest`

### Frontend Development
1. Make changes to TypeScript/React files in `frontend/src/`
2. Vite provides hot module replacement
3. TypeScript compilation happens in real-time
4. Run tests: `cd frontend && npm run test`

### Database Development
- MongoDB data persists in Docker volumes
- Redis data is ephemeral by default
- Use MongoDB Compass or similar tools to inspect data

## Migration Status

This project structure represents the initial setup for migrating from Streamlit to FastAPI + React. The existing TradingAgents functionality will be gradually integrated into this new architecture while maintaining backward compatibility.

### Completed
- ✅ Project structure initialization
- ✅ FastAPI backend skeleton
- ✅ React frontend skeleton
- ✅ Development environment setup
- ✅ Docker configuration
- ✅ Basic tooling and configuration

### Next Steps
- 🔄 FastAPI application basic structure (Task 2.1)
- 🔄 Database connections and models (Task 2.2)
- 🔄 Authentication and authorization (Task 2.3)
- 🔄 Core API implementation (Task 3.x)
- 🔄 Frontend components and pages (Task 5.x)

## Contributing

1. Follow the existing code structure and naming conventions
2. Use TypeScript for all frontend code
3. Use type hints for all Python code
4. Write tests for new functionality
5. Update documentation as needed

## Support

For questions about the project structure or development setup, please refer to:
- Backend README: `backend/README.md`
- Frontend README: `frontend/README.md`
- Original project documentation in `docs/`