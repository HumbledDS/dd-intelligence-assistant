"""Data Acquisition Engine package for DD Intelligence Assistant."""

__version__ = "0.1.0"

# Core components
from .core import (
    BaseCollector,
    CollectionResult,
    RateLimiter,
    CircuitBreaker,
    RetryHandler,
    EventRouter,
    DataCollectionScheduler
)

# Collectors
from .collectors import (
    InseeCollector,
    InfogreffeCollector,
    DataGouvCollector
)

# Main engine
from .DataAcquisitionEngine import DataAcquisitionEngine, create_data_acquisition_engine

# Configuration
from .config.settings import settings

__all__ = [
    # Core components
    "BaseCollector",
    "CollectionResult",
    "RateLimiter",
    "CircuitBreaker",
    "RetryHandler",
    "EventRouter",
    "DataCollectionScheduler",
    
    # Collectors
    "InseeCollector",
    "InfogreffeCollector",
    "DataGouvCollector",
    
    # Main engine
    "DataAcquisitionEngine",
    "create_data_acquisition_engine",
    
    # Configuration
    "settings",
    
    # Version
    "__version__"
]
