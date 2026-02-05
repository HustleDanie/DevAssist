"""Core data models for the migration workflow."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from pathlib import Path


class MigrationStatus(str, Enum):
    """Status of a migration operation."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


class MigrationType(str, Enum):
    """Type of migration to perform."""

    PY2_TO_PY3 = "py2to3"
    FLASK_TO_FASTAPI = "flask_to_fastapi"


@dataclass
class CodeLocation:
    """Location of code within a file."""

    file_path: Path
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


@dataclass
class DeprecatedPattern:
    """A deprecated code pattern identified by the Planner agent."""

    pattern_id: str
    pattern_type: str
    description: str
    location: CodeLocation
    original_code: str
    severity: str = "warning"  # info, warning, error
    suggested_fix: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeChange:
    """A code change proposed by the Coder agent."""

    change_id: str
    pattern_id: str
    file_path: Path
    original_code: str
    new_code: str
    start_line: int
    end_line: int
    explanation: str
    confidence: float = 1.0
    applied: bool = False


@dataclass
class TestResult:
    """Result of a test run by the Tester agent."""

    test_id: str
    test_name: str
    passed: bool
    execution_time: float
    error_message: str = ""
    stdout: str = ""
    stderr: str = ""
    coverage: float = 0.0


@dataclass
class MigrationState:
    """
    State object passed through the LangGraph workflow.
    
    This contains all the information needed to track migration progress
    across the Planner, Coder, and Tester agents.
    """

    # Repository information
    repo_url: str
    repo_path: Path | None = None
    branch_name: str = ""

    # Migration configuration
    migration_type: MigrationType = MigrationType.PY2_TO_PY3
    status: MigrationStatus = MigrationStatus.PENDING

    # Files to process
    files_to_migrate: list[Path] = field(default_factory=list)
    files_processed: list[Path] = field(default_factory=list)

    # Planner agent outputs
    deprecated_patterns: list[DeprecatedPattern] = field(default_factory=list)

    # Coder agent outputs
    code_changes: list[CodeChange] = field(default_factory=list)
    applied_changes: list[CodeChange] = field(default_factory=list)

    # Tester agent outputs
    test_results: list[TestResult] = field(default_factory=list)
    tests_passed: bool = False

    # Workflow state
    current_agent: str = ""
    iteration: int = 0
    max_iterations: int = 3
    errors: list[str] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)

    # MCP context
    style_guide_context: str = ""

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the workflow history."""
        self.messages.append({"role": role, "content": content})

    def add_error(self, error: str) -> None:
        """Add an error to the error list."""
        self.errors.append(error)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the migration state."""
        return {
            "repo_url": self.repo_url,
            "status": self.status.value,
            "migration_type": self.migration_type.value,
            "files_processed": len(self.files_processed),
            "patterns_found": len(self.deprecated_patterns),
            "changes_applied": len(self.applied_changes),
            "tests_passed": self.tests_passed,
            "errors": len(self.errors),
        }


@dataclass
class MigrationResult:
    """Final result of a migration operation."""

    success: bool
    state: MigrationState
    pr_url: str = ""
    summary: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "pr_url": self.pr_url,
            "summary": self.summary,
            "duration_seconds": self.duration_seconds,
            "state_summary": self.state.get_summary(),
        }
