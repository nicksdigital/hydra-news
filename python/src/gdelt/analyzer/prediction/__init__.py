"""
GDELT Prediction Package

This package provides functionality for predicting future events based on patterns in news coverage.
"""

from .predictor import PredictiveEventDetector
from .models import PredictionModels
from .visualizer import PredictionVisualizer
from .report_generator import PredictionReportGenerator

__all__ = [
    'PredictiveEventDetector',
    'PredictionModels',
    'PredictionVisualizer',
    'PredictionReportGenerator'
]
