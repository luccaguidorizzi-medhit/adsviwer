"""
Vercel Serverless Entrypoint for Adsviwer / Mundo Revalida Competitor Intelligence
Author: Lagana Flow
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.app import app
