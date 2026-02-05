"""
DevAssist - Multi-Agent Code Migration Tool

An enterprise-grade multi-agent system for automated code migration
(Python 2→3, Flask→FastAPI) across repositories.
"""

__version__ = "0.1.0"
__author__ = "DevAssist Team"

from devassist.agents.workflow import MigrationWorkflow
from devassist.core.config import Settings

__all__ = ["MigrationWorkflow", "Settings", "__version__"]
