"""
LangGraph Workflow - Orchestrates the multi-agent migration pipeline.

This module defines the state graph that coordinates the Planner, Coder,
and Tester agents in a structured workflow.
"""

from typing import Literal
from pathlib import Path
import time

from langgraph.graph import StateGraph, END

from devassist.core.models import (
    MigrationState,
    MigrationStatus,
    MigrationType,
    MigrationResult,
)
from devassist.agents.planner import PlannerAgent
from devassist.agents.coder import CoderAgent
from devassist.agents.tester import TesterAgent
from devassist.github import GitHubManager
from devassist.core.config import get_settings


class MigrationWorkflow:
    """
    LangGraph workflow orchestrating the migration pipeline.
    
    The workflow follows this pattern:
    1. Clone repository
    2. Planner identifies deprecated patterns
    3. Coder rewrites code
    4. Tester validates changes
    5. If tests fail and iterations remain, loop back to Coder
    6. Create pull request with changes
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        self.github = GitHubManager()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        # Create the graph with MigrationState
        workflow = StateGraph(MigrationState)

        # Add nodes for each agent
        workflow.add_node("clone", self._clone_repo)
        workflow.add_node("planner", self._run_planner)
        workflow.add_node("coder", self._run_coder)
        workflow.add_node("tester", self._run_tester)
        workflow.add_node("create_pr", self._create_pr)
        workflow.add_node("finalize", self._finalize)

        # Set the entry point
        workflow.set_entry_point("clone")

        # Add edges
        workflow.add_edge("clone", "planner")
        workflow.add_edge("planner", "coder")
        workflow.add_edge("coder", "tester")
        
        # Conditional edge based on test results
        workflow.add_conditional_edges(
            "tester",
            self._should_retry_or_finish,
            {
                "retry": "coder",
                "create_pr": "create_pr",
                "fail": "finalize",
            }
        )
        
        workflow.add_edge("create_pr", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _clone_repo(self, state: MigrationState) -> MigrationState:
        """Clone the repository and discover files to migrate."""
        state.add_message("system", f"Cloning repository: {state.repo_url}")
        
        try:
            # Clean up any existing work directory to avoid file lock issues
            work_dir = Path(self.settings.work_dir)
            if work_dir.exists():
                import shutil
                import subprocess
                import platform
                
                # Try multiple cleanup methods for Windows file locks
                try:
                    shutil.rmtree(work_dir, ignore_errors=True)
                except Exception:
                    pass
                
                # If still exists, use OS-specific forceful delete
                if work_dir.exists() and platform.system() == "Windows":
                    try:
                        subprocess.run(
                            ["cmd", "/c", "rmdir", "/s", "/q", str(work_dir)],
                            capture_output=True,
                            timeout=30
                        )
                    except Exception:
                        pass
                
                # Final attempt with retry
                import time
                for _ in range(3):
                    if not work_dir.exists():
                        break
                    try:
                        shutil.rmtree(work_dir, ignore_errors=False)
                    except Exception:
                        time.sleep(1)
            
            # Clone using GitHub manager
            state.repo_path = self.github.clone_repository(
                state.repo_url,
                self.settings.work_dir
            )
            
            # Create migration branch
            state.branch_name = self.settings.target_branch
            self.github.create_branch(state.repo_path, state.branch_name)

            # Discover Python files
            state.files_to_migrate = list(self._discover_files(state.repo_path))
            
            state.add_message(
                "system",
                f"Found {len(state.files_to_migrate)} Python files to analyze."
            )
        except Exception as e:
            state.add_error(f"Failed to clone repository: {str(e)}")
            state.status = MigrationStatus.FAILED

        return state

    def _discover_files(self, repo_path: Path) -> iter:
        """
        Discover Python files in the repository using a generator.
        
        Args:
            repo_path: Path to the repository
            
        Yields:
            Path objects for each Python file
        """
        for path in repo_path.rglob("*.py"):
            # Skip common non-source directories
            parts = path.parts
            skip_dirs = {
                ".git", ".venv", "venv", "__pycache__", 
                "node_modules", ".tox", "build", "dist"
            }
            if not any(part in skip_dirs for part in parts):
                yield path

    def _run_planner(self, state: MigrationState) -> MigrationState:
        """Run the Planner agent."""
        if state.status == MigrationStatus.FAILED:
            return state
        return self.planner.run(state)

    def _run_coder(self, state: MigrationState) -> MigrationState:
        """Run the Coder agent."""
        if state.status == MigrationStatus.FAILED:
            return state
        return self.coder.run(state)

    def _run_tester(self, state: MigrationState) -> MigrationState:
        """Run the Tester agent."""
        if state.status == MigrationStatus.FAILED:
            return state
        state.iteration += 1
        return self.tester.run(state)

    def _should_retry_or_finish(
        self, state: MigrationState
    ) -> Literal["retry", "create_pr", "fail"]:
        """
        Determine the next step based on test results.
        
        Returns:
            "retry" if tests failed but retries remain
            "create_pr" if tests passed
            "fail" if max retries exceeded
        """
        if state.status == MigrationStatus.FAILED:
            return "fail"
        
        if state.tests_passed:
            return "create_pr"
        
        if state.iteration < state.max_iterations:
            state.add_message(
                "system",
                f"Tests failed, attempting retry {state.iteration + 1}/{state.max_iterations}"
            )
            return "retry"
        
        return "fail"

    def _create_pr(self, state: MigrationState) -> MigrationState:
        """Create a pull request with the changes."""
        if not self.settings.auto_create_pr:
            state.add_message("system", "Auto PR creation disabled, skipping.")
            return state

        state.status = MigrationStatus.REVIEW
        state.add_message("system", "Creating pull request...")

        try:
            pr_url = self.github.create_pull_request(
                repo_path=state.repo_path,
                branch_name=state.branch_name,
                title=f"[DevAssist] {state.migration_type.value} Migration",
                body=self._generate_pr_body(state),
            )
            state.add_message("system", f"Pull request created: {pr_url}")
        except Exception as e:
            state.add_error(f"Failed to create PR: {str(e)}")

        return state

    def _generate_pr_body(self, state: MigrationState) -> str:
        """Generate the pull request body with migration details."""
        summary = state.get_summary()
        
        body = f"""## 🔄 DevAssist Migration Report

### Migration Type
{state.migration_type.value}

### Summary
- **Files Processed:** {summary['files_processed']}
- **Patterns Found:** {summary['patterns_found']}
- **Changes Applied:** {summary['changes_applied']}
- **Tests Passed:** {'✅ Yes' if summary['tests_passed'] else '❌ No'}

### Changes Made
"""
        for change in state.applied_changes[:10]:  # Limit to first 10
            body += f"\n- `{change.file_path}`: {change.explanation}"
        
        if len(state.applied_changes) > 10:
            body += f"\n- ... and {len(state.applied_changes) - 10} more changes"

        body += """

### Testing
This migration was validated with automated tests.

---
*Generated by [DevAssist](https://github.com/your-org/devassist) - Multi-Agent Code Migration Tool*
"""
        return body

    def _finalize(self, state: MigrationState) -> MigrationState:
        """Finalize the migration workflow."""
        if state.tests_passed:
            state.status = MigrationStatus.COMPLETED
            state.add_message("system", "Migration completed successfully!")
        else:
            state.status = MigrationStatus.FAILED
            state.add_message("system", "Migration failed. Please review errors.")

        return state

    def run(
        self, repo_url: str, migration_type: str = "py2to3"
    ) -> MigrationResult:
        """
        Run the migration workflow.
        
        Args:
            repo_url: URL of the repository to migrate
            migration_type: Type of migration ("py2to3" or "flask_to_fastapi")
            
        Returns:
            MigrationResult with the outcome
        """
        start_time = time.time()

        # Initialize state
        initial_state = MigrationState(
            repo_url=repo_url,
            migration_type=MigrationType(migration_type),
        )

        # Run the workflow
        # LangGraph returns a dict-like object, we need to handle both cases
        final_state_data = self.graph.invoke(initial_state)
        
        # Handle the result - it could be a dict or MigrationState
        if isinstance(final_state_data, dict):
            # LangGraph returns dict, reconstruct the state
            final_state = MigrationState(
                repo_url=final_state_data.get('repo_url', repo_url),
                migration_type=final_state_data.get('migration_type', MigrationType(migration_type)),
            )
            # Copy over the relevant fields
            final_state.repo_path = final_state_data.get('repo_path')
            final_state.branch_name = final_state_data.get('branch_name', '')
            final_state.status = final_state_data.get('status', MigrationStatus.FAILED)
            final_state.files_to_migrate = final_state_data.get('files_to_migrate', [])
            final_state.files_processed = final_state_data.get('files_processed', [])
            final_state.deprecated_patterns = final_state_data.get('deprecated_patterns', [])
            final_state.code_changes = final_state_data.get('code_changes', [])
            final_state.applied_changes = final_state_data.get('applied_changes', [])
            final_state.test_results = final_state_data.get('test_results', [])
            final_state.tests_passed = final_state_data.get('tests_passed', False)
            final_state.current_agent = final_state_data.get('current_agent', '')
            final_state.iteration = final_state_data.get('iteration', 0)
            final_state.errors = final_state_data.get('errors', [])
            final_state.messages = final_state_data.get('messages', [])
        else:
            final_state = final_state_data

        duration = time.time() - start_time

        return MigrationResult(
            success=final_state.status == MigrationStatus.COMPLETED,
            state=final_state,
            summary=f"Migration {'completed' if final_state.tests_passed else 'failed'} "
                   f"in {duration:.2f}s",
            duration_seconds=duration,
        )
