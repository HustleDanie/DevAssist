"""
Planner Agent - Identifies deprecated code patterns in the codebase.

This agent uses AST analysis and LLM reasoning to identify code patterns
that need to be migrated (e.g., Python 2 syntax, Flask patterns).
"""

from typing import Any, Generator
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from devassist.core.models import (
    MigrationState,
    MigrationStatus,
    MigrationType,
    DeprecatedPattern,
    CodeLocation,
)
from devassist.ast_parser import ASTAnalyzer
from devassist.core.config import get_settings


class PlannerAgent:
    """
    Agent 1: Planner - Identifies deprecated code patterns.
    
    The Planner agent is responsible for:
    1. Scanning the codebase for files to migrate
    2. Using AST analysis to identify deprecated patterns
    3. Using LLM to understand complex deprecation scenarios (optional)
    4. Prioritizing patterns by severity and impact
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.llm = None
        self.llm_available = False
        
        # Only initialize LLM if API key is set and non-empty
        api_key = settings.openai_api_key
        if api_key and len(api_key) > 10 and not api_key.startswith("your-"):
            try:
                self.llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=api_key,
                    temperature=0.1,  # Low temperature for consistent analysis
                )
                self.llm_available = True
            except Exception as e:
                print(f"[PLANNER] LLM initialization failed: {e}")
                self.llm_available = False
        else:
            print("[PLANNER] Running in AST-only mode (no OpenAI API key configured)")
        
        self.ast_analyzer = ASTAnalyzer()
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the Planner agent."""
        return """You are an expert code analyst specializing in code migration.
Your role is to identify deprecated code patterns that need to be updated.

For Python 2 to 3 migrations, look for:
- print statements (print "x" instead of print("x"))
- xrange() usage (should be range())
- unicode/str handling issues
- dict.keys(), .values(), .items() returning lists
- except Exception, e: syntax
- raw_input() usage
- __future__ imports that can be removed

For Flask to FastAPI migrations, look for:
- @app.route() decorators (should be @app.get(), @app.post(), etc.)
- Flask request object usage
- Flask Response objects
- Blueprint patterns
- Flask-specific extensions

Provide your analysis in a structured format with:
1. Pattern type
2. File location (path, line numbers)
3. Original code snippet
4. Severity (info, warning, error)
5. Suggested fix approach

Be thorough but avoid false positives. Focus on actual migration issues."""

    def analyze_file_patterns(
        self, file_path: str, content: str, migration_type: MigrationType
    ) -> Generator[DeprecatedPattern, None, None]:
        """
        Analyze a single file for deprecated patterns using generators.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file
            migration_type: Type of migration to perform
            
        Yields:
            DeprecatedPattern objects for each identified issue
        """
        # First, use AST analysis for structural patterns
        ast_patterns = self.ast_analyzer.analyze(content, migration_type)
        
        for pattern in ast_patterns:
            pattern.location.file_path = file_path
            yield pattern

        # Then use LLM for complex patterns that AST might miss (if available)
        if self.llm_available:
            llm_patterns = self._analyze_with_llm(file_path, content, migration_type)
            
            for pattern in llm_patterns:
                yield pattern

    def _analyze_with_llm(
        self, file_path: str, content: str, migration_type: MigrationType
    ) -> Generator[DeprecatedPattern, None, None]:
        """Use LLM to identify complex patterns that AST might miss."""
        if not self.llm_available or not self.llm:
            return
            
        migration_context = (
            "Python 2 to Python 3" if migration_type == MigrationType.PY2_TO_PY3
            else "Flask to FastAPI"
        )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Analyze this code for {migration_context} migration issues.

File: {file_path}

```python
{content}
```

List each issue you find with:
- Pattern type
- Line number(s)
- Code snippet
- Severity
- Suggested approach

If no issues found, respond with "NO_ISSUES_FOUND".""")
        ]

        response = self.llm.invoke(messages)
        patterns = self._parse_llm_response(response.content, file_path, content)
        
        for pattern in patterns:
            yield pattern

    def _parse_llm_response(
        self, response: str, file_path: str, content: str
    ) -> Generator[DeprecatedPattern, None, None]:
        """Parse LLM response into DeprecatedPattern objects."""
        if "NO_ISSUES_FOUND" in response:
            return

        # Simple parsing - in production, use structured output
        lines = content.split("\n")
        pattern_id = 0
        
        # Parse each identified pattern from the response
        current_pattern: dict[str, Any] = {}
        
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("- Pattern type:"):
                if current_pattern:
                    yield self._create_pattern(current_pattern, file_path, lines, pattern_id)
                    pattern_id += 1
                current_pattern = {"type": line.split(":", 1)[1].strip()}
            elif line.startswith("- Line number"):
                try:
                    line_num = int("".join(filter(str.isdigit, line.split(":", 1)[1])))
                    current_pattern["line"] = line_num
                except (ValueError, IndexError):
                    current_pattern["line"] = 1
            elif line.startswith("- Code snippet:"):
                current_pattern["code"] = line.split(":", 1)[1].strip()
            elif line.startswith("- Severity:"):
                current_pattern["severity"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("- Suggested"):
                current_pattern["suggestion"] = line.split(":", 1)[1].strip()

        if current_pattern:
            yield self._create_pattern(current_pattern, file_path, lines, pattern_id)

    def _create_pattern(
        self, data: dict[str, Any], file_path: str, lines: list[str], pattern_id: int
    ) -> DeprecatedPattern:
        """Create a DeprecatedPattern from parsed data."""
        line_num = data.get("line", 1)
        return DeprecatedPattern(
            pattern_id=f"llm_{pattern_id}",
            pattern_type=data.get("type", "unknown"),
            description=data.get("suggestion", ""),
            location=CodeLocation(
                file_path=file_path,
                start_line=line_num,
                end_line=line_num,
            ),
            original_code=data.get("code", lines[line_num - 1] if line_num <= len(lines) else ""),
            severity=data.get("severity", "warning"),
            suggested_fix=data.get("suggestion", ""),
        )

    def run(self, state: MigrationState) -> MigrationState:
        """
        Run the Planner agent on the current migration state.
        
        Args:
            state: Current migration state
            
        Returns:
            Updated migration state with identified patterns
        """
        state.status = MigrationStatus.PLANNING
        state.current_agent = "planner"
        state.add_message("system", "Planner agent starting analysis...")

        all_patterns: list[DeprecatedPattern] = []

        # Process files using generator for memory efficiency
        for file_path in state.files_to_migrate:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Use generator to stream patterns
                for pattern in self.analyze_file_patterns(
                    str(file_path), content, state.migration_type
                ):
                    all_patterns.append(pattern)

            except Exception as e:
                state.add_error(f"Error analyzing {file_path}: {str(e)}")

        state.deprecated_patterns = all_patterns
        state.add_message(
            "planner",
            f"Analysis complete. Found {len(all_patterns)} deprecated patterns."
        )

        return state
