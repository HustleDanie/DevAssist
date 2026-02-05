"""Tests for GitHub integration module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from devassist.github.manager import GitHubManager
from devassist.github.pr_generator import PRGenerator
from devassist.core.models import MigrationState, MigrationStatus, MigrationType


class TestGitHubManager:
    """Tests for GitHubManager class."""

    def test_extract_repo_name_https(self):
        """Test extracting repo name from HTTPS URL."""
        with patch('devassist.github.manager.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                github_token="test-token",
                github_base_url="https://api.github.com"
            )
            
            manager = GitHubManager()
            
            name = manager._extract_repo_name("https://github.com/owner/repo.git")
            assert name == "repo"
            
            name = manager._extract_repo_name("https://github.com/owner/repo")
            assert name == "repo"

    def test_extract_repo_name_ssh(self):
        """Test extracting repo name from SSH URL."""
        with patch('devassist.github.manager.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                github_token="test-token",
                github_base_url="https://api.github.com"
            )
            
            manager = GitHubManager()
            
            name = manager._extract_repo_name("git@github.com:owner/repo.git")
            assert name == "repo"

    def test_get_authenticated_url(self):
        """Test getting authenticated URL."""
        with patch('devassist.github.manager.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                github_token="test-token",
                github_base_url="https://api.github.com"
            )
            
            manager = GitHubManager()
            
            url = manager._get_authenticated_url("https://github.com/owner/repo")
            assert "test-token" in url

    def test_get_authenticated_url_no_token(self):
        """Test authenticated URL without token."""
        with patch('devassist.github.manager.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                github_token="",
                github_base_url="https://api.github.com"
            )
            
            manager = GitHubManager()
            
            url = manager._get_authenticated_url("https://github.com/owner/repo")
            assert url == "https://github.com/owner/repo"

    def test_parse_remote_url_https(self):
        """Test parsing HTTPS remote URL."""
        with patch('devassist.github.manager.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                github_token="test-token",
                github_base_url="https://api.github.com"
            )
            
            manager = GitHubManager()
            
            owner, repo = manager._parse_remote_url("https://github.com/owner/repo.git")
            assert owner == "owner"
            assert repo == "repo"

    def test_parse_remote_url_ssh(self):
        """Test parsing SSH remote URL."""
        with patch('devassist.github.manager.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                github_token="test-token",
                github_base_url="https://api.github.com"
            )
            
            manager = GitHubManager()
            
            owner, repo = manager._parse_remote_url("git@github.com:owner/repo.git")
            assert owner == "owner"
            assert repo == "repo"


class TestPRGenerator:
    """Tests for PRGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PRGenerator()

    def test_generate_title_py2to3(self):
        """Test generating title for Python 2 to 3 migration."""
        state = MigrationState(
            repo_url="https://github.com/test/repo",
            migration_type=MigrationType.PY2_TO_PY3,
        )
        
        title = self.generator.generate_title(state)
        
        assert "Python 2 to 3" in title
        assert "DevAssist" in title

    def test_generate_title_flask_to_fastapi(self):
        """Test generating title for Flask to FastAPI migration."""
        state = MigrationState(
            repo_url="https://github.com/test/repo",
            migration_type=MigrationType.FLASK_TO_FASTAPI,
        )
        
        title = self.generator.generate_title(state)
        
        assert "Flask to FastAPI" in title

    def test_generate_body(self):
        """Test generating PR body."""
        state = MigrationState(
            repo_url="https://github.com/test/repo",
            migration_type=MigrationType.PY2_TO_PY3,
            status=MigrationStatus.COMPLETED,
        )
        state.tests_passed = True
        
        body = self.generator.generate_body(state)
        
        assert "Summary" in body
        assert "Migration Type" in body
        assert "py2to3" in body

    def test_generate_commit_message(self):
        """Test generating commit message."""
        state = MigrationState(
            repo_url="https://github.com/test/repo",
            migration_type=MigrationType.PY2_TO_PY3,
        )
        
        message = self.generator.generate_commit_message(state)
        
        assert "DevAssist" in message

    def test_generate_commit_message_detailed(self):
        """Test generating detailed commit message."""
        state = MigrationState(
            repo_url="https://github.com/test/repo",
            migration_type=MigrationType.PY2_TO_PY3,
        )
        state.files_processed = [Path("file1.py")]
        
        message = self.generator.generate_commit_message(state, detailed=True)
        
        assert "DevAssist" in message
        assert "Migration Summary" in message
