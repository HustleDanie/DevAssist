"""
Coder Agent - Rewrites deprecated code following migration patterns.

This agent takes the patterns identified by the Planner and generates
the updated code following best practices and style guides.

Integrates with MCP (Model Context Protocol) to pull context from
internal documentation wikis to ensure new code follows company style guides.
"""

import asyncio
from typing import Generator
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from devassist.core.models import (
    MigrationState,
    MigrationStatus,
    MigrationType,
    DeprecatedPattern,
    CodeChange,
)
from devassist.core.config import get_settings
from devassist.mcp.client import MCPClient
from devassist.ast_parser.transformers import Py2to3Transformer, FlaskToFastAPITransformer


class CoderAgent:
    """
    Agent 2: Coder - Rewrites deprecated code.
    
    The Coder agent is responsible for:
    1. Taking deprecated patterns from the Planner
    2. Generating updated code following migration rules
    3. Ensuring code follows style guides (via MCP context)
    4. Applying changes to files
    
    MCP Integration:
    - Fetches style guides from documentation servers
    - Retrieves migration-specific guidance
    - Ensures code follows company standards
    
    Supports AST-only mode when LLM is not available.
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
                    temperature=0.2,  # Slightly higher for creative solutions
                )
                self.llm_available = True
            except Exception as e:
                print(f"[CODER] LLM initialization failed: {e}")
                self.llm_available = False
        else:
            print("[CODER] Running in AST-only mode (no OpenAI API key configured)")
        
        self.mcp_client = MCPClient()
        # AST transformers for LLM-free mode
        self.py2to3_transformer = Py2to3Transformer()
        self.flask_transformer = FlaskToFastAPITransformer()
        self.system_prompt = self._build_system_prompt()
        self._style_guide_cache: str = ""
        self._migration_guide_cache: dict = {}

    async def fetch_mcp_context(self, migration_type: MigrationType) -> str:
        """
        Fetch style guide and migration context from MCP server.
        
        This pulls context from internal documentation wikis to ensure
        the new code follows company style guides.
        
        Args:
            migration_type: Type of migration being performed
            
        Returns:
            Combined context string for LLM prompt
        """
        context_parts = []
        
        try:
            async with self.mcp_client as client:
                # Fetch Python style guide
                style_guide = await client.get_style_guide("python")
                if style_guide:
                    self._style_guide_cache = style_guide
                    context_parts.append(f"## Company Style Guide\n{style_guide}")
                
                # Fetch migration-specific guide
                if migration_type == MigrationType.PY2_TO_PY3:
                    guide = await client.get_migration_guide("python2", "python3")
                else:
                    guide = await client.get_migration_guide("flask", "fastapi")
                
                if guide:
                    self._migration_guide_cache = guide
                    patterns = guide.get("patterns", [])
                    if patterns:
                        context_parts.append("## Migration Patterns")
                        for p in patterns[:10]:  # Limit to top 10
                            context_parts.append(f"- {p.get('name', '')}: {p.get('description', '')}")
                
        except Exception as e:
            # MCP is optional - continue without it
            print(f"MCP context fetch failed (optional): {e}")
        
        return "\n\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the Coder agent."""
        return """You are an expert code migration engineer.
Your role is to rewrite deprecated code patterns with modern equivalents.

Guidelines:
1. Preserve the original logic and behavior
2. Follow the target framework's best practices
3. Maintain code readability and documentation
4. Add type hints where appropriate
5. Ensure backward compatibility when possible

For Python 2 to 3 migrations:
- Convert print statements to print() functions
- Replace xrange() with range()
- Update unicode/str handling
- Convert dict.iteritems() to dict.items()
- Update exception syntax: except E as e:
- Replace raw_input() with input()
- Update division behavior if needed

For Flask to FastAPI migrations:
- Convert @app.route() to @app.get(), @app.post(), etc.
- Replace Flask request with FastAPI dependency injection
- Convert Flask Response to FastAPI Response
- Update Blueprint to APIRouter
- Add Pydantic models for request/response validation
- Use async/await where beneficial

Return ONLY the new code, no explanations. The code should be a drop-in replacement."""

    def generate_fix(
        self, pattern: DeprecatedPattern, file_content: str, migration_type: MigrationType,
        style_guide: str = ""
    ) -> CodeChange:
        """
        Generate a fix for a single deprecated pattern.
        
        Uses LLM if available, otherwise falls back to AST transformation.
        
        Args:
            pattern: The deprecated pattern to fix
            file_content: Full content of the file
            migration_type: Type of migration
            style_guide: Optional style guide context from MCP
            
        Returns:
            CodeChange object with the proposed fix
        """
        # If LLM is not available, use AST-based transformation
        if not self.llm_available:
            return self._generate_fix_with_ast(pattern, file_content, migration_type)
        
        context_start = max(0, pattern.location.start_line - 5)
        context_end = min(len(file_content.split("\n")), pattern.location.end_line + 5)
        lines = file_content.split("\n")
        context = "\n".join(lines[context_start:context_end])

        migration_context = (
            "Python 2 to Python 3" if migration_type == MigrationType.PY2_TO_PY3
            else "Flask to FastAPI"
        )

        style_context = f"\n\nStyle Guide Requirements:\n{style_guide}" if style_guide else ""

        messages = [
            SystemMessage(content=self.system_prompt + style_context),
            HumanMessage(content=f"""Rewrite this {migration_context} code.

Pattern Type: {pattern.pattern_type}
Issue: {pattern.description}

Original Code (lines {pattern.location.start_line}-{pattern.location.end_line}):
```python
{pattern.original_code}
```

Context:
```python
{context}
```

Provide only the replacement code for the original snippet.""")
        ]

        response = self.llm.invoke(messages)
        new_code = self._clean_code_response(response.content)

        return CodeChange(
            change_id=f"change_{pattern.pattern_id}",
            pattern_id=pattern.pattern_id,
            file_path=pattern.location.file_path,
            original_code=pattern.original_code,
            new_code=new_code,
            start_line=pattern.location.start_line,
            end_line=pattern.location.end_line,
            explanation=f"Migration fix for {pattern.pattern_type}: {pattern.description}",
            confidence=0.9,
        )

    def _generate_fix_with_ast(
        self, pattern: DeprecatedPattern, file_content: str, migration_type: MigrationType
    ) -> CodeChange:
        """
        Generate a fix using AST transformation (no LLM needed).
        
        Args:
            pattern: The deprecated pattern to fix
            file_content: Full content of the file
            migration_type: Type of migration
            
        Returns:
            CodeChange object with the proposed fix
        """
        # Use the appropriate AST transformer
        if migration_type == MigrationType.PY2_TO_PY3:
            transformed, changes = self.py2to3_transformer.transform(file_content)
        else:
            transformed, changes = self.flask_transformer.transform(file_content)
        
        # For syntax_error patterns or file_error patterns, replace the entire file
        # since the transformation is file-wide
        if pattern.pattern_type in ("syntax_error", "file_error"):
            original_lines = file_content.split("\n")
            return CodeChange(
                change_id=f"change_{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                file_path=pattern.location.file_path,
                original_code=file_content,
                new_code=transformed,
                start_line=1,
                end_line=len(original_lines),
                explanation=f"Full file migration (regex-based): {', '.join(changes[:5])}",
                confidence=0.90,
            )
        
        # Extract just the changed lines for comparison
        original_lines = file_content.split("\n")
        transformed_lines = transformed.split("\n")
        
        # Get the new code for the pattern's line range
        start_idx = max(0, pattern.location.start_line - 1)
        end_idx = min(len(transformed_lines), pattern.location.end_line)
        new_code = "\n".join(transformed_lines[start_idx:end_idx])
        
        explanation = f"AST-based migration fix for {pattern.pattern_type}"
        if changes:
            explanation += f" (changes: {', '.join(changes[:3])})"
        
        return CodeChange(
            change_id=f"change_{pattern.pattern_id}",
            pattern_id=pattern.pattern_id,
            file_path=pattern.location.file_path,
            original_code=pattern.original_code,
            new_code=new_code,
            start_line=pattern.location.start_line,
            end_line=pattern.location.end_line,
            explanation=explanation,
            confidence=0.95,  # Higher confidence for deterministic AST transforms
        )

    def _clean_code_response(self, response: str) -> str:
        """Clean the LLM response to extract just the code."""
        # Remove markdown code blocks if present
        code = response.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line (```python) and last line (```)
            code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        return code.strip()

    def generate_fixes(
        self, patterns: list[DeprecatedPattern], file_contents: dict[str, str],
        migration_type: MigrationType, style_guide: str = ""
    ) -> Generator[CodeChange, None, None]:
        """
        Generate fixes for multiple patterns using a generator.
        
        Args:
            patterns: List of deprecated patterns to fix
            file_contents: Dictionary mapping file paths to their contents
            migration_type: Type of migration
            style_guide: Optional style guide context
            
        Yields:
            CodeChange objects for each pattern
        """
        for pattern in patterns:
            file_path = str(pattern.location.file_path)
            if file_path in file_contents:
                change = self.generate_fix(
                    pattern, file_contents[file_path], migration_type, style_guide
                )
                yield change

    def apply_changes(
        self, changes: list[CodeChange], file_contents: dict[str, str]
    ) -> dict[str, str]:
        """
        Apply code changes to file contents.
        
        Args:
            changes: List of changes to apply
            file_contents: Dictionary mapping file paths to contents
            
        Returns:
            Updated file contents dictionary
        """
        # Group changes by file
        changes_by_file: dict[str, list[CodeChange]] = {}
        for change in changes:
            file_path = str(change.file_path)
            if file_path not in changes_by_file:
                changes_by_file[file_path] = []
            changes_by_file[file_path].append(change)

        # Apply changes to each file (in reverse order to preserve line numbers)
        updated_contents = file_contents.copy()
        
        for file_path, file_changes in changes_by_file.items():
            if file_path not in updated_contents:
                continue
                
            lines = updated_contents[file_path].split("\n")
            
            # Sort changes by start line in reverse order
            sorted_changes = sorted(file_changes, key=lambda c: c.start_line, reverse=True)
            
            for change in sorted_changes:
                # Replace the lines
                start_idx = change.start_line - 1
                end_idx = change.end_line
                new_lines = change.new_code.split("\n")
                lines = lines[:start_idx] + new_lines + lines[end_idx:]
                change.applied = True

            updated_contents[file_path] = "\n".join(lines)

        return updated_contents

    def run(self, state: MigrationState) -> MigrationState:
        """
        Run the Coder agent on the current migration state.
        
        Fetches style guide context from MCP server to ensure code
        follows company standards, then generates and applies fixes.
        
        Args:
            state: Current migration state with patterns from Planner
            
        Returns:
            Updated migration state with code changes
        """
        state.status = MigrationStatus.CODING
        state.current_agent = "coder"
        state.add_message("system", "Coder agent generating fixes...")

        if not state.deprecated_patterns:
            state.add_message("coder", "No patterns to fix.")
            return state

        # Fetch MCP context for style guides (if not already cached)
        if not state.style_guide_context:
            try:
                # Run async MCP fetch in sync context
                loop = asyncio.new_event_loop()
                state.style_guide_context = loop.run_until_complete(
                    self.fetch_mcp_context(state.migration_type)
                )
                loop.close()
                if state.style_guide_context:
                    state.add_message("coder", "Loaded style guide context from MCP server")
            except Exception as e:
                state.add_message("coder", f"MCP context unavailable (optional): {e}")

        # Load file contents
        file_contents: dict[str, str] = {}
        for pattern in state.deprecated_patterns:
            file_path = str(pattern.location.file_path)
            if file_path not in file_contents:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_contents[file_path] = f.read()
                except Exception as e:
                    state.add_error(f"Error reading {file_path}: {str(e)}")

        # Generate fixes using generator
        changes = list(self.generate_fixes(
            state.deprecated_patterns,
            file_contents,
            state.migration_type,
            state.style_guide_context
        ))

        state.code_changes = changes

        # Apply changes
        updated_contents = self.apply_changes(changes, file_contents)
        
        # Write updated files
        for file_path, content in updated_contents.items():
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                state.applied_changes.extend(
                    [c for c in changes if str(c.file_path) == file_path and c.applied]
                )
            except Exception as e:
                state.add_error(f"Error writing {file_path}: {str(e)}")

        state.add_message(
            "coder",
            f"Applied {len(state.applied_changes)} code changes across "
            f"{len(updated_contents)} files."
        )

        return state
