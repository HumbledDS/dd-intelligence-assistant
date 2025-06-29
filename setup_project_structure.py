#!/usr/bin/env python3
"""
Project Structure Setup Script for DD Intelligence Assistant
Generates the complete file and folder architecture
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

class ProjectStructureGenerator:
    """Generates the complete project structure with boilerplate files"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.created_files = []
        self.created_dirs = []
    
    def create_directory_structure(self):
        """Create the main directory structure"""
        
        directories = [
            # Root level directories
            "docs",
            "scripts",
            "docker",
            "terraform",
            "kubernetes",
            
            # Data Acquisition Engine
            "data_acquisition_engine",
            "data_acquisition_engine/config",
            "data_acquisition_engine/core",
            "data_acquisition_engine/collectors",
            "data_acquisition_engine/collectors/official",
            "data_acquisition_engine/collectors/financial",
            "data_acquisition_engine/collectors/alternative",
            "data_acquisition_engine/collectors/news",
            "data_acquisition_engine/processors",
            "data_acquisition_engine/validators",
            "data_acquisition_engine/storage",
            "data_acquisition_engine/monitoring",
            "data_acquisition_engine/utils",
            "data_acquisition_engine/tests",
            "data_acquisition_engine/tests/unit",
            "data_acquisition_engine/tests/integration",
            "data_acquisition_engine/tests/performance",
            
            # RAG Pipeline
            "rag_pipeline",
            "rag_pipeline/embeddings",
            "rag_pipeline/retrieval",
            "rag_pipeline/vector_store",
            "rag_pipeline/chunking",
            "rag_pipeline/reranking",
            "rag_pipeline/tests",
            
            # LLM Orchestration
            "llm_orchestration",
            "llm_orchestration/providers",
            "llm_orchestration/prompts",
            "llm_orchestration/quality_assurance",
            "llm_orchestration/routing",
            "llm_orchestration/tests",
            
            # Report Generation
            "report_generation",
            "report_generation/templates",
            "report_generation/exporters",
            "report_generation/formatters",
            "report_generation/tests",
            
            # API Services
            "api_services",
            "api_services/auth",
            "api_services/endpoints",
            "api_services/middleware",
            "api_services/websockets",
            "api_services/tests",
            
            # Frontend
            "frontend",
            "frontend/src",
            "frontend/src/components",
            "frontend/src/pages",
            "frontend/src/hooks",
            "frontend/src/services",
            "frontend/src/utils",
            "frontend/public",
            "frontend/tests",
            
            # Shared utilities
            "shared",
            "shared/database",
            "shared/monitoring",
            "shared/security",
            "shared/config",
            "shared/utils",
            "shared/tests",
            
            # Deployment and operations
            "deployments",
            "deployments/aws",
            "deployments/gcp",
            "deployments/azure",
            "deployments/local",
            
            # Monitoring and observability
            "monitoring",
            "monitoring/grafana",
            "monitoring/prometheus",
            "monitoring/alerts",
            
            # Data pipeline orchestration
            "orchestration",
            "orchestration/airflow",
            "orchestration/airflow/dags",
            "orchestration/airflow/plugins",
            "orchestration/dbt",
            "orchestration/dbt/models",
            "orchestration/dbt/macros",
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
    
    def create_python_files(self):
        """Create Python files with boilerplate content"""
        
        python_files = {
            # Data Acquisition Engine
            "data_acquisition_engine/__init__.py": self.get_package_init("Data Acquisition Engine"),
            "data_acquisition_engine/config/__init__.py": "",
            "data_acquisition_engine/config/settings.py": self.get_settings_template(),
            "data_acquisition_engine/core/__init__.py": "",
            "data_acquisition_engine/core/base_collector.py": self.get_base_collector_template(),
            "data_acquisition_engine/core/scheduler.py": self.get_scheduler_template(),
            "data_acquisition_engine/core/rate_limiter.py": self.get_rate_limiter_template(),
            "data_acquisition_engine/core/circuit_breaker.py": self.get_circuit_breaker_template(),
            "data_acquisition_engine/core/retry_handler.py": self.get_retry_handler_template(),
            "data_acquisition_engine/core/event_router.py": self.get_event_router_template(),
            
            # Collectors
            "data_acquisition_engine/collectors/__init__.py": "",
            "data_acquisition_engine/collectors/official/__init__.py": "",
            "data_acquisition_engine/collectors/official/insee_collector.py": self.get_insee_collector_template(),
            "data_acquisition_engine/collectors/official/infogreffe_collector.py": self.get_infogreffe_collector_template(),
            "data_acquisition_engine/collectors/official/datagouv_collector.py": self.get_datagouv_collector_template(),
            
            "data_acquisition_engine/collectors/financial/__init__.py": "",
            "data_acquisition_engine/collectors/financial/bloomberg_collector.py": self.get_bloomberg_collector_template(),
            "data_acquisition_engine/collectors/financial/factset_collector.py": self.get_factset_collector_template(),
            
            "data_acquisition_engine/collectors/alternative/__init__.py": "",
            "data_acquisition_engine/collectors/alternative/glassdoor_collector.py": self.get_glassdoor_collector_template(),
            "data_acquisition_engine/collectors/alternative/linkedin_collector.py": self.get_linkedin_collector_template(),
            
            "data_acquisition_engine/collectors/news/__init__.py": "",
            "data_acquisition_engine/collectors/news/google_news_collector.py": self.get_google_news_collector_template(),
            "data_acquisition_engine/collectors/news/rss_collector.py": self.get_rss_collector_template(),
            
            # Processors
            "data_acquisition_engine/processors/__init__.py": "",
            "data_acquisition_engine/processors/document_parser.py": self.get_document_parser_template(),
            "data_acquisition_engine/processors/entity_extractor.py": self.get_entity_extractor_template(),
            
            # Validators
            "data_acquisition_engine/validators/__init__.py": "",
            "data_acquisition_engine/validators/schema_validator.py": self.get_schema_validator_template(),
            "data_acquisition_engine/validators/quality_checker.py": self.get_quality_checker_template(),
            
            # Storage
            "data_acquisition_engine/storage/__init__.py": "",
            "data_acquisition_engine/storage/data_lake_writer.py": self.get_data_lake_writer_template(),
            "data_acquisition_engine/storage/metadata_store.py": self.get_metadata_store_template(),
            
            # Monitoring
            "data_acquisition_engine/monitoring/__init__.py": "",
            "data_acquisition_engine/monitoring/metrics_collector.py": self.get_metrics_collector_template(),
            "data_acquisition_engine/monitoring/health_checker.py": self.get_health_checker_template(),
            
            # Utils
            "data_acquisition_engine/utils/__init__.py": "",
            "data_acquisition_engine/utils/logging_config.py": self.get_logging_config_template(),
            "data_acquisition_engine/utils/security_utils.py": self.get_security_utils_template(),
            
            # Tests
            "data_acquisition_engine/tests/__init__.py": "",
            "data_acquisition_engine/tests/conftest.py": self.get_pytest_conftest_template(),
            "data_acquisition_engine/tests/unit/test_base_collector.py": self.get_test_base_collector_template(),
            "data_acquisition_engine/tests/integration/test_insee_integration.py": self.get_test_insee_integration_template(),
            
            # RAG Pipeline
            "rag_pipeline/__init__.py": self.get_package_init("RAG Pipeline"),
            "rag_pipeline/embeddings/__init__.py": "",
            "rag_pipeline/embeddings/embedding_manager.py": self.get_embedding_manager_template(),
            "rag_pipeline/retrieval/__init__.py": "",
            "rag_pipeline/retrieval/retriever.py": self.get_retriever_template(),
            "rag_pipeline/vector_store/__init__.py": "",
            "rag_pipeline/vector_store/vector_store_manager.py": self.get_vector_store_template(),
            
            # API Services
            "api_services/__init__.py": self.get_package_init("API Services"),
            "api_services/main.py": self.get_fastapi_main_template(),
            "api_services/auth/__init__.py": "",
            "api_services/auth/authentication.py": self.get_auth_template(),
            "api_services/endpoints/__init__.py": "",
            "api_services/endpoints/companies.py": self.get_companies_endpoint_template(),
            "api_services/endpoints/reports.py": self.get_reports_endpoint_template(),
            
            # Shared utilities
            "shared/__init__.py": self.get_package_init("Shared Utilities"),
            "shared/database/__init__.py": "",
            "shared/database/connection.py": self.get_database_connection_template(),
            "shared/config/__init__.py": "",
            "shared/config/base_config.py": self.get_base_config_template(),
        }
        
        for file_path, content in python_files.items():
            full_path = self.project_root / file_path
            full_path.write_text(content, encoding='utf-8')
            self.created_files.append(str(full_path))
            print(f"Created file: {full_path}")
    
    def create_config_files(self):
        """Create configuration files"""
        
        config_files = {
            # YAML configuration files
            "data_acquisition_engine/config/sources.yaml": self.get_sources_config_template(),
            "data_acquisition_engine/config/rate_limits.yaml": self.get_rate_limits_config_template(),
            "data_acquisition_engine/config/quality_rules.yaml": self.get_quality_rules_config_template(),
            
            # Docker files
            "docker/Dockerfile.data-acquisition": self.get_dockerfile_data_acquisition_template(),
            "docker/Dockerfile.api": self.get_dockerfile_api_template(),
            "docker/docker-compose.yml": self.get_docker_compose_template(),
            "docker/docker-compose.dev.yml": self.get_docker_compose_dev_template(),
            
            # Requirements files
            "requirements.txt": self.get_requirements_template(),
            "requirements-dev.txt": self.get_requirements_dev_template(),
            "data_acquisition_engine/requirements.txt": self.get_data_acquisition_requirements_template(),
            
            # Environment files
            ".env.example": self.get_env_example_template(),
            ".env.local.example": self.get_env_local_example_template(),
            
            # CI/CD files
            ".github/workflows/ci.yml": self.get_github_ci_template(),
            ".github/workflows/cd.yml": self.get_github_cd_template(),
            ".github/PULL_REQUEST_TEMPLATE.md": self.get_pr_template(),
            ".github/ISSUE_TEMPLATE/bug_report.md": self.get_bug_report_template(),
            ".github/ISSUE_TEMPLATE/feature_request.md": self.get_feature_request_template(),
            
            # Project files
            "setup.py": self.get_setup_py_template(),
            "pyproject.toml": self.get_pyproject_toml_template(),
            "Makefile": self.get_makefile_template(),
            ".gitignore": self.get_gitignore_template(),
            ".pre-commit-config.yaml": self.get_precommit_config_template(),
            
            # Documentation
            "README.md": self.get_readme_template(),
            "CONTRIBUTING.md": self.get_contributing_template(),
            "docs/architecture.md": self.get_architecture_doc_template(),
            "docs/api_documentation.md": self.get_api_doc_template(),
            "docs/deployment_guide.md": self.get_deployment_guide_template(),
            
            # Terraform
            "terraform/main.tf": self.get_terraform_main_template(),
            "terraform/variables.tf": self.get_terraform_variables_template(),
            "terraform/outputs.tf": self.get_terraform_outputs_template(),
            
            # Kubernetes
            "kubernetes/namespace.yaml": self.get_k8s_namespace_template(),
            "kubernetes/deployment.yaml": self.get_k8s_deployment_template(),
            "kubernetes/service.yaml": self.get_k8s_service_template(),
            
            # Airflow
            "orchestration/airflow/dags/dd_intelligence_dag.py": self.get_airflow_dag_template(),
            "orchestration/airflow/requirements.txt": self.get_airflow_requirements_template(),
            
            # dbt
            "orchestration/dbt/dbt_project.yml": self.get_dbt_project_template(),
            "orchestration/dbt/models/schema.yml": self.get_dbt_schema_template(),
            
            # Monitoring
            "monitoring/prometheus/prometheus.yml": self.get_prometheus_config_template(),
            "monitoring/grafana/dashboards/dd-intelligence.json": self.get_grafana_dashboard_template(),
        }
        
        for file_path, content in config_files.items():
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            self.created_files.append(str(full_path))
            print(f"Created file: {full_path}")
    
    def create_frontend_files(self):
        """Create frontend structure and files"""
        
        # Create additional frontend directories
        frontend_dirs = [
            "frontend/src/components/common",
            "frontend/src/components/dashboard",
            "frontend/src/components/reports",
            "frontend/src/components/companies",
            "frontend/src/pages/dashboard",
            "frontend/src/pages/reports",
            "frontend/src/pages/companies",
            "frontend/src/styles",
            "frontend/src/assets",
        ]
        
        for directory in frontend_dirs:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        frontend_files = {
            "frontend/package.json": self.get_package_json_template(),
            "frontend/tsconfig.json": self.get_tsconfig_template(),
            "frontend/next.config.js": self.get_next_config_template(),
            "frontend/tailwind.config.js": self.get_tailwind_config_template(),
            "frontend/.env.local.example": self.get_frontend_env_template(),
            "frontend/src/pages/index.tsx": self.get_index_page_template(),
            "frontend/src/pages/_app.tsx": self.get_app_page_template(),
            "frontend/src/components/layout/Layout.tsx": self.get_layout_component_template(),
            "frontend/src/styles/globals.css": self.get_global_styles_template(),
        }
        
        for file_path, content in frontend_files.items():
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            self.created_files.append(str(full_path))
            print(f"Created file: {full_path}")
    
    def generate_summary(self):
        """Generate a summary of created files and directories"""
        
        summary = f"""
# Project Structure Generation Complete

## Summary
- **Directories created**: {len(self.created_dirs)}
- **Files created**: {len(self.created_files)}

## Next Steps

1. **Initialize git repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial project structure"
   ```

2. **Create feature branches**:
   ```bash
   git checkout -b feature/data-acquisition-engine
   git checkout -b origin/develop
   git checkout -b origin/main 
   ```
"""
        return summary

    def get_package_init(self, package_name: str) -> str:
        return f'"""{package_name} package for DD Intelligence Assistant."""\n\n__version__ = "0.1.0"\n'

    def get_settings_template(self) -> str:
        return '''"""
Configuration settings for data acquisition engine.
"""
import os
from typing import Dict, Any
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/dd_intelligence"
    redis_url: str = "redis://localhost:6379/0"
    
    # External APIs
    insee_api_key: str = ""
    openai_api_key: str = ""
    bloomberg_api_key: str = ""
    
    # Rate limiting
    default_rate_limit: int = 100  # requests per minute
    
    # Security
    secret_key: str = "your-secret-key-here"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
'''

    def get_base_collector_template(self) -> str:
        return '''"""
Base collector abstract class for data acquisition engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CollectionResult:
    """Standard result format for all collectors"""
    source: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    quality_score: float
    collection_timestamp: datetime
    errors: List[str]
    warnings: List[str]

class BaseCollector(ABC):
    """Abstract base class for all data collectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limiter = self._init_rate_limiter()
        self.circuit_breaker = self._init_circuit_breaker()
        self.retry_handler = self._init_retry_handler()

    @abstractmethod
    async def collect(self, target: str, **kwargs) -> CollectionResult:
        """Main collection method - must be implemented by subclasses"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate collector configuration"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the data source is accessible"""
        pass

    def _init_rate_limiter(self):
        """Initialize rate limiter based on config"""
        # TODO: Implement rate limiter initialization
        pass

    def _init_circuit_breaker(self):
        """Initialize circuit breaker for fault tolerance"""
        # TODO: Implement circuit breaker initialization
        pass

    def _init_retry_handler(self):
        """Initialize retry handler with exponential backoff"""
        # TODO: Implement retry handler initialization
        pass
'''

    def get_scheduler_template(self):
        return "# scheduler.py placeholder\n"

    def get_rate_limiter_template(self):
        return "# rate_limiter.py placeholder\n"

    def get_circuit_breaker_template(self):
        return "# circuit_breaker.py placeholder\n"

    def get_retry_handler_template(self):
        return "# retry_handler.py placeholder\n"

    def get_event_router_template(self):
        return "# event_router.py placeholder\n"

    def get_insee_collector_template(self):
        return "# insee_collector.py placeholder\n"

    def get_infogreffe_collector_template(self):
        return "# infogreffe_collector.py placeholder\n"

    def get_datagouv_collector_template(self):
        return "# datagouv_collector.py placeholder\n"

    def get_bloomberg_collector_template(self):
        return "# bloomberg_collector.py placeholder\n"

    def get_factset_collector_template(self):
        return "# factset_collector.py placeholder\n"

    def get_glassdoor_collector_template(self):
        return "# glassdoor_collector.py placeholder\n"

    def get_linkedin_collector_template(self):
        return "# linkedin_collector.py placeholder\n"

    def get_google_news_collector_template(self):
        return "# google_news_collector.py placeholder\n"

    def get_rss_collector_template(self):
        return "# rss_collector.py placeholder\n"

    def get_document_parser_template(self):
        return "# document_parser.py placeholder\n"

    def get_entity_extractor_template(self):
        return "# entity_extractor.py placeholder\n"

    def get_schema_validator_template(self):
        return "# schema_validator.py placeholder\n"

    def get_quality_checker_template(self):
        return "# quality_checker.py placeholder\n"

    def get_data_lake_writer_template(self):
        return "# data_lake_writer.py placeholder\n"

    def get_metadata_store_template(self):
        return "# metadata_store.py placeholder\n"

    def get_metrics_collector_template(self):
        return "# metrics_collector.py placeholder\n"

    def get_health_checker_template(self):
        return "# health_checker.py placeholder\n"

    def get_logging_config_template(self):
        return "# logging_config.py placeholder\n"

    def get_security_utils_template(self):
        return "# security_utils.py placeholder\n"

    def get_pytest_conftest_template(self):
        return "# conftest.py placeholder\n"

    def get_test_base_collector_template(self):
        return "# test_base_collector.py placeholder\n"

    def get_test_insee_integration_template(self):
        return "# test_insee_integration.py placeholder\n"

    def get_embedding_manager_template(self):
        return "# embedding_manager.py placeholder\n"

    def get_retriever_template(self):
        return "# retriever.py placeholder\n"

    def get_vector_store_template(self):
        return "# vector_store_manager.py placeholder\n"

    def get_fastapi_main_template(self):
        return "# main.py placeholder\n"

    def get_auth_template(self):
        return "# authentication.py placeholder\n"

    def get_companies_endpoint_template(self):
        return "# companies.py placeholder\n"

    def get_reports_endpoint_template(self):
        return "# reports.py placeholder\n"

    def get_database_connection_template(self):
        return "# connection.py placeholder\n"

    def get_base_config_template(self):
        return "# base_config.py placeholder\n"

    def get_sources_config_template(self):
        return "# sources.yaml placeholder\n"

    def get_rate_limits_config_template(self):
        return "# rate_limits.yaml placeholder\n"

    def get_quality_rules_config_template(self):
        return "# quality_rules.yaml placeholder\n"

    def get_dockerfile_data_acquisition_template(self):
        return "# Dockerfile.data-acquisition placeholder\n"

    def get_dockerfile_api_template(self):
        return "# Dockerfile.api placeholder\n"

    def get_docker_compose_template(self):
        return "# docker-compose.yml placeholder\n"

    def get_docker_compose_dev_template(self):
        return "# docker-compose.dev.yml placeholder\n"

    def get_requirements_template(self) -> str:
        return '''# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
redis==5.0.1

# Data processing
pandas==2.1.3
numpy==1.25.2
python-dateutil==2.8.2

# HTTP client
httpx==0.25.2
aiohttp==3.9.1
requests==2.31.0

# Web scraping
beautifulsoup4==4.12.2
selenium==4.15.2
scrapy==2.11.0

# Document processing
PyPDF2==3.0.1
python-docx==1.1.0
openpyxl==3.1.2

# ML and NLP
transformers==4.35.2
sentence-transformers==2.2.2
spacy==3.7.2
openai==1.3.7

# Vector databases
pinecone-client==2.2.4
weaviate-client==3.25.3

# Monitoring and logging
prometheus-client==0.19.0
structlog==23.2.0

# Task queue
celery==5.3.4
flower==2.0.1

# Configuration
python-dotenv==1.0.0
pyyaml==6.0.1

# Testing (moved to requirements-dev.txt)
'''

    def get_requirements_dev_template(self) -> str:
        return '''# Include production requirements
-r requirements.txt

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.2

# Code quality
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
bandit==1.7.5

# Pre-commit hooks
pre-commit==3.5.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.4.8

# Development tools
ipython==8.17.2
jupyter==1.0.0
'''

    def get_data_acquisition_requirements_template(self):
        return "# data_acquisition_engine/requirements.txt placeholder\n"

    def get_env_example_template(self):
        return "# .env.example placeholder\n"

    def get_env_local_example_template(self):
        return "# .env.local.example placeholder\n"

    def get_github_ci_template(self):
        return "# .github/workflows/ci.yml placeholder\n"

    def get_github_cd_template(self):
        return "# .github/workflows/cd.yml placeholder\n"

    def get_pr_template(self):
        return "# .github/PULL_REQUEST_TEMPLATE.md placeholder\n"

    def get_bug_report_template(self):
        return "# .github/ISSUE_TEMPLATE/bug_report.md placeholder\n"

    def get_feature_request_template(self):
        return "# .github/ISSUE_TEMPLATE/feature_request.md placeholder\n"

    def get_setup_py_template(self):
        return "# setup.py placeholder\n"

    def get_pyproject_toml_template(self):
        return "# pyproject.toml placeholder\n"

    def get_makefile_template(self):
        return "# Makefile placeholder\n"

    def get_gitignore_template(self):
        return "# .gitignore placeholder\n"

    def get_precommit_config_template(self):
        return "# .pre-commit-config.yaml placeholder\n"

    def get_readme_template(self) -> str:
        return '''# Due Diligence Intelligence Assistant

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
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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
'''

    def get_architecture_doc_template(self):
        return "# docs/architecture.md placeholder\n"

    def get_api_doc_template(self):
        return "# docs/api_documentation.md placeholder\n"

    def get_deployment_guide_template(self):
        return "# docs/deployment_guide.md placeholder\n"

    def get_terraform_main_template(self):
        return "# terraform/main.tf placeholder\n"

    def get_terraform_variables_template(self):
        return "# terraform/variables.tf placeholder\n"

    def get_terraform_outputs_template(self):
        return "# terraform/outputs.tf placeholder\n"

    def get_k8s_namespace_template(self):
        return "# kubernetes/namespace.yaml placeholder\n"

    def get_k8s_deployment_template(self):
        return "# kubernetes/deployment.yaml placeholder\n"

    def get_k8s_service_template(self):
        return "# kubernetes/service.yaml placeholder\n"

    def get_airflow_dag_template(self):
        return "# orchestration/airflow/dags/dd_intelligence_dag.py placeholder\n"

    def get_airflow_requirements_template(self):
        return "# orchestration/airflow/requirements.txt placeholder\n"

    def get_dbt_project_template(self):
        return "# orchestration/dbt/dbt_project.yml placeholder\n"

    def get_dbt_schema_template(self):
        return "# orchestration/dbt/models/schema.yml placeholder\n"

    def get_prometheus_config_template(self):
        return "# monitoring/prometheus/prometheus.yml placeholder\n"

    def get_grafana_dashboard_template(self):
        return "# monitoring/grafana/dashboards/dd-intelligence.json placeholder\n"

    def get_package_json_template(self):
        return '{\n  "name": "frontend",\n  "version": "0.1.0"\n}\n'

    def get_tsconfig_template(self):
        return '{\n  "compilerOptions": {}\n}\n'

    def get_next_config_template(self):
        return '// next.config.js placeholder\n'

    def get_tailwind_config_template(self):
        return '// tailwind.config.js placeholder\n'

    def get_frontend_env_template(self):
        return '# .env.local.example placeholder\n'

    def get_index_page_template(self):
        return '// index.tsx placeholder\n'

    def get_app_page_template(self):
        return '// _app.tsx placeholder\n'

    def get_layout_component_template(self):
        return '// Layout.tsx placeholder\n'

    def get_global_styles_template(self):
        return '/* globals.css placeholder */\n'

    def get_contributing_template(self):
        return "# CONTRIBUTING.md placeholder\n"


def main():
    """Main execution function"""
    print("🚀 Starting DD Intelligence Assistant Project Structure Generation...")
    
    generator = ProjectStructureGenerator()
    
    print("\n📁 Creating directory structure...")
    generator.create_directory_structure()
    
    print("\n🐍 Creating Python files...")
    generator.create_python_files()
    
    print("\n⚙️ Creating configuration files...")
    generator.create_config_files()
    
    print("\n🎨 Creating frontend files...")
    generator.create_frontend_files()
    
    print("\n" + "="*60)
    print(generator.generate_summary())
    print("="*60)
    print("\n✅ Project structure generation completed successfully!")


if __name__ == "__main__":
    main()
