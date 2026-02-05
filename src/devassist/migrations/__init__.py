"""
Migrations module - Migration patterns and transformations.

Contains specific migration implementations for:
- Python 2 to Python 3
- Flask to FastAPI
"""

from devassist.migrations.py2to3 import Py2to3Migration
from devassist.migrations.flask_to_fastapi import FlaskToFastAPIMigration

__all__ = ["Py2to3Migration", "FlaskToFastAPIMigration"]
