"""
GitHub integration module - API integration for repository operations.

Provides functionality for:
- Cloning repositories
- Creating branches
- Committing changes
- Creating pull requests
"""

from devassist.github.manager import GitHubManager
from devassist.github.pr_generator import PRGenerator

__all__ = ["GitHubManager", "PRGenerator"]
