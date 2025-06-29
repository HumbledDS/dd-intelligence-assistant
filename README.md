# Due Diligence Intelligence Assistant

AI-powered due diligence automation platform for management consulting

## Overview
The Due Diligence Intelligence Assistant transforms traditional due diligence processes through advanced AI automation, reducing comprehensive analysis time from weeks to hours while maintaining professional-grade quality.

## Key Features
- **Automated Data Collection**: Integrates with French business registries (INSEE, Infogreffe) and financial data providers
- **AI-Powered Analysis**: Advanced RAG (Retrieval-Augmented Generation) for intelligent document analysis
- **Professional Reports**: Automated generation of comprehensive due diligence reports
- **Interactive Chat**: Natural language interface for exploring analysis results
- **Multi-Format Export**: PDF reports and PowerPoint presentations

## Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Data Acquisition│───▶│ RAG Pipeline    │───▶│ Report          │
│ Engine          │    │                 │    │ Generation      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ French Business │    │ Vector Database │    │ API Services    │
│ Data Sources    │    │ (Pinecone)      │    │ (FastAPI)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- PostgreSQL
- Redis

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/dd-intelligence-assistant.git
cd dd-intelligence-assistant
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
cd ..
```

5. Set up pre-commit hooks:
```bash
pre-commit install
```

## Development

Start the backend:
```bash
uvicorn api_services.main:app --reload --port 8000
```

Start the frontend (in another terminal):
```bash
cd frontend
npm run dev
```

Run tests:
```bash
pytest
```

## Project Structure
```
dd-intelligence-assistant/
├── data_acquisition_engine/    # Data collection and processing
├── rag_pipeline/              # Retrieval-Augmented Generation
├── llm_orchestration/         # LLM integration and management
├── api_services/              # REST API backend
├── frontend/                  # Next.js React frontend
├── shared/                    # Shared utilities
├── docs/                      # Documentation
├── docker/                    # Container definitions
├── terraform/                 # Infrastructure as Code
└── tests/                     # Test suites
```
