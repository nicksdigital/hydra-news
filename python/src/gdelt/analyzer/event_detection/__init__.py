"""
GDELT Event Detection Package

This package provides functionality for detecting events in GDELT news data.
"""

from .base_event_detector import BaseEventDetector
from .anomaly_detector import AnomalyDetector
from .burst_detector import BurstDetector
from .correlation_analyzer import CorrelationAnalyzer
from .entity_event_detector import EntityEventDetector
from .multi_entity_detector import MultiEntityEventDetector

__all__ = [
    'BaseEventDetector',
    'AnomalyDetector',
    'BurstDetector',
    'CorrelationAnalyzer',
    'EntityEventDetector',
    'MultiEntityEventDetector'
]
