"""Tests for the multi-agent workflow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from devassist.core.models import (
    MigrationState,
    MigrationStatus,
    MigrationType,
    DeprecatedPattern,
    CodeLocation,
    CodeChange,
)


class TestMigrationState:
    """Tests for MigrationState model."""

    def test_initial_state(self):
        """Test initial migration state creation."""
        state = MigrationState(repo_url="https://github.com/test/repo")
        
        assert state.repo_url == "https://github.com/test/repo"
        assert state.status == MigrationStatus.PENDING
        assert state.migration_type == MigrationType.PY2_TO_PY3
        assert len(state.files_to_migrate) == 0
        assert len(state.deprecated_patterns) == 0

    def test_add_message(self):
        """Test adding messages to state."""
        state = MigrationState(repo_url="https://github.com/test/repo")
        
        state.add_message("system", "Test message")
        
        assert len(state.messages) == 1
        assert state.messages[0]["role"] == "system"
        assert state.messages[0]["content"] == "Test message"

    def test_add_error(self):
        """Test adding errors to state."""
        state = MigrationState(repo_url="https://github.com/test/repo")
        
        state.add_error("Test error")
        
        assert len(state.errors) == 1
        assert state.errors[0] == "Test error"

    def test_get_summary(self):
        """Test getting state summary."""
        state = MigrationState(
            repo_url="https://github.com/test/repo",
            status=MigrationStatus.COMPLETED,
        )
        state.files_processed = [Path("file1.py"), Path("file2.py")]
        state.deprecated_patterns = [
            DeprecatedPattern(
                pattern_id="1",
                pattern_type="test",
                description="test",
                location=CodeLocation(file_path=Path(""), start_line=1, end_line=1),
                original_code="test",
            )
        ]
        state.tests_passed = True
        
        summary = state.get_summary()
        
        assert summary["files_processed"] == 2
        assert summary["patterns_found"] == 1
        assert summary["tests_passed"] is True


class TestDeprecatedPattern:
    """Tests for DeprecatedPattern model."""

    def test_pattern_creation(self):
        """Test creating a deprecated pattern."""
        pattern = DeprecatedPattern(
            pattern_id="test_1",
            pattern_type="xrange_usage",
            description="xrange is not available in Python 3",
            location=CodeLocation(
                file_path=Path("test.py"),
                start_line=10,
                end_line=10,
            ),
            original_code="for i in xrange(10):",
            severity="warning",
            suggested_fix="Replace with range()",
        )
        
        assert pattern.pattern_id == "test_1"
        assert pattern.pattern_type == "xrange_usage"
        assert pattern.severity == "warning"
        assert pattern.location.start_line == 10


class TestCodeChange:
    """Tests for CodeChange model."""

    def test_change_creation(self):
        """Test creating a code change."""
        change = CodeChange(
            change_id="change_1",
            pattern_id="pattern_1",
            file_path=Path("test.py"),
            original_code="xrange(10)",
            new_code="range(10)",
            start_line=10,
            end_line=10,
            explanation="Replaced xrange with range",
        )
        
        assert change.change_id == "change_1"
        assert change.original_code == "xrange(10)"
        assert change.new_code == "range(10)"
        assert change.applied is False


class TestPlannerAgent:
    """Tests for the Planner agent."""

    @patch('devassist.agents.planner.ChatOpenAI')
    def test_planner_initialization(self, mock_openai):
        """Test Planner agent initialization."""
        from devassist.agents.planner import PlannerAgent
        
        with patch('devassist.agents.planner.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                openai_api_key="test-key",
                openai_model="gpt-4"
            )
            
            planner = PlannerAgent()
            
            assert planner.system_prompt is not None
            assert "deprecated" in planner.system_prompt.lower()

    @patch('devassist.agents.planner.ChatOpenAI')
    def test_planner_analyze_file_patterns(self, mock_openai):
        """Test analyzing file patterns."""
        from devassist.agents.planner import PlannerAgent
        
        with patch('devassist.agents.planner.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                openai_api_key="test-key",
                openai_model="gpt-4"
            )
            
            planner = PlannerAgent()
            
            source = """
for i in xrange(10):
    print(i)
"""
            patterns = list(planner.analyze_file_patterns(
                "test.py", source, MigrationType.PY2_TO_PY3
            ))
            
            # Should find at least the xrange pattern from AST analysis
            assert len(patterns) >= 1


class TestCoderAgent:
    """Tests for the Coder agent."""

    @patch('devassist.agents.coder.ChatOpenAI')
    def test_coder_initialization(self, mock_openai):
        """Test Coder agent initialization."""
        from devassist.agents.coder import CoderAgent
        
        with patch('devassist.agents.coder.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                openai_api_key="test-key",
                openai_model="gpt-4"
            )
            
            coder = CoderAgent()
            
            assert coder.system_prompt is not None
            assert "rewrite" in coder.system_prompt.lower() or "migration" in coder.system_prompt.lower()

    def test_coder_clean_code_response(self):
        """Test cleaning code from LLM response."""
        from devassist.agents.coder import CoderAgent
        
        with patch('devassist.agents.coder.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                openai_api_key="test-key",
                openai_model="gpt-4"
            )
            
            with patch('devassist.agents.coder.ChatOpenAI'):
                coder = CoderAgent()
                
                # Test removing markdown code blocks
                response = "```python\nfor i in range(10):\n    print(i)\n```"
                cleaned = coder._clean_code_response(response)
                
                assert "```" not in cleaned
                assert "for i in range(10)" in cleaned


class TestTesterAgent:
    """Tests for the Tester agent."""

    @patch('devassist.agents.tester.ChatOpenAI')
    def test_tester_initialization(self, mock_openai):
        """Test Tester agent initialization."""
        from devassist.agents.tester import TesterAgent
        
        with patch('devassist.agents.tester.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                openai_api_key="test-key",
                openai_model="gpt-4",
                docker_enabled=True,
                docker_image="python:3.11-slim"
            )
            
            tester = TesterAgent()
            
            assert tester.system_prompt is not None
            assert "test" in tester.system_prompt.lower()
            assert tester.docker_enabled is True
