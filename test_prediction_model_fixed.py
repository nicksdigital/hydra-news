#!/usr/bin/env python3
# Comprehensive test for the prediction model in the Hydra News system
# This script tests the news event prediction model with different parameters

import os
import sys
import argparse
import logging
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/prediction_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("prediction_test")

# Create directories needed
os.makedirs('logs', exist_ok=True)
os.makedirs('test_results/prediction', exist_ok=True)

# Set path to include the src directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

# Create a simple mock database manager for testing
class MockDBManager:
    def __init__(self):
        self.conn = None
        self.cursor = None

# Import