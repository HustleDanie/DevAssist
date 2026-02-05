"""
Pattern Matcher - Configurable pattern matching for migrations.

This module provides a flexible pattern matching system that can be
extended with custom patterns for different migration scenarios.
"""

import re
from dataclasses import dataclass, field
from typing import Callable, Generator
from pathlib import Path

from devassist.core.models import DeprecatedPattern, CodeLocation


@dataclass
class PatternRule:
    """A configurable pattern matching rule."""
    
    pattern_id: str
    pattern_type: str
    description: str
    
    # Matching can be regex-based or AST-based
    regex_pattern: str | None = None
    ast_node_type: str | None = None
    
    # Condition function for complex matching
    condition: Callable[[str, int], bool] | None = None
    
    severity: str = "warning"
    suggested_fix: str = ""
    metadata: dict = field(default_factory=dict)


class PatternMatcher:
    """
    Configurable pattern matcher supporting multiple matching strategies.
    
    Supports:
    - Regex-based pattern matching
    - AST node type matching
    - Custom condition functions
    - Combination of multiple strategies
    """

    def __init__(self) -> None:
        self.rules: list[PatternRule] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default pattern rules for common migrations."""
        # Python 2 to 3 regex patterns
        py2_patterns = [
            PatternRule(
                pattern_id="print_stmt",
                pattern_type="print_statement",
                description="Python 2 print statement",
                regex_pattern=r"^\s*print\s+[^(]",
                severity="error",
                suggested_fix="Convert to print() function"
            ),
            PatternRule(
                pattern_id="except_comma",
                pattern_type="except_comma_syntax",
                description="Python 2 except syntax with comma",
                regex_pattern=r"except\s+\w+\s*,\s*\w+\s*:",
                severity="error",
                suggested_fix="Use 'except Exception as e:' syntax"
            ),
            PatternRule(
                pattern_id="backtick_repr",
                pattern_type="backtick_repr",
                description="Python 2 backtick repr syntax",
                regex_pattern=r"`[^`]+`",
                severity="error",
                suggested_fix="Use repr() function instead"
            ),
            PatternRule(
                pattern_id="octal_literal",
                pattern_type="octal_literal",
                description="Python 2 octal literal (0NNN)",
                regex_pattern=r"\b0[0-7]+\b(?!o)",
                severity="warning",
                suggested_fix="Use 0oNNN octal syntax"
            ),
            PatternRule(
                pattern_id="ur_string",
                pattern_type="ur_string_prefix",
                description="Python 2 ur'' string prefix",
                regex_pattern=r'\bur["\']',
                severity="error",
                suggested_fix="ur'' is not valid in Python 3"
            ),
        ]
        
        # Flask to FastAPI regex patterns
        flask_patterns = [
            PatternRule(
                pattern_id="flask_run",
                pattern_type="flask_run",
                description="Flask app.run() call",
                regex_pattern=r"\.run\s*\([^)]*debug\s*=",
                severity="info",
                suggested_fix="Use uvicorn.run() or command line: uvicorn app:app --reload"
            ),
            PatternRule(
                pattern_id="flask_config",
                pattern_type="flask_config",
                description="Flask app.config usage",
                regex_pattern=r"app\.config\[",
                severity="warning",
                suggested_fix="Use Pydantic Settings for configuration"
            ),
            PatternRule(
                pattern_id="flask_secret_key",
                pattern_type="flask_secret_key",
                description="Flask secret key configuration",
                regex_pattern=r"app\.secret_key\s*=",
                severity="warning",
                suggested_fix="Use environment variables for secrets"
            ),
            PatternRule(
                pattern_id="flask_before_request",
                pattern_type="flask_before_request",
                description="Flask before_request decorator",
                regex_pattern=r"@\w+\.before_request",
                severity="warning",
                suggested_fix="Use FastAPI middleware or dependencies"
            ),
            PatternRule(
                pattern_id="flask_after_request",
                pattern_type="flask_after_request",
                description="Flask after_request decorator",
                regex_pattern=r"@\w+\.after_request",
                severity="warning",
                suggested_fix="Use FastAPI middleware"
            ),
        ]
        
        self.rules.extend(py2_patterns)
        self.rules.extend(flask_patterns)

    def add_rule(self, rule: PatternRule) -> None:
        """Add a custom pattern rule."""
        self.rules.append(rule)

    def remove_rule(self, pattern_id: str) -> bool:
        """Remove a pattern rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.pattern_id == pattern_id:
                del self.rules[i]
                return True
        return False

    def match(
        self, source: str, file_path: Path | None = None
    ) -> Generator[DeprecatedPattern, None, None]:
        """
        Match patterns against source code.
        
        Args:
            source: Source code to analyze
            file_path: Optional file path for location info
            
        Yields:
            DeprecatedPattern for each match found
        """
        lines = source.split("\n")
        
        for rule in self.rules:
            yield from self._match_rule(rule, lines, file_path)

    def _match_rule(
        self, rule: PatternRule, lines: list[str], file_path: Path | None
    ) -> Generator[DeprecatedPattern, None, None]:
        """Match a single rule against source lines."""
        if rule.regex_pattern:
            pattern = re.compile(rule.regex_pattern)
            
            for line_num, line in enumerate(lines, start=1):
                match = pattern.search(line)
                if match:
                    # Check custom condition if provided
                    if rule.condition and not rule.condition(line, line_num):
                        continue
                    
                    yield DeprecatedPattern(
                        pattern_id=f"{rule.pattern_id}_{line_num}",
                        pattern_type=rule.pattern_type,
                        description=rule.description,
                        location=CodeLocation(
                            file_path=file_path or Path(""),
                            start_line=line_num,
                            end_line=line_num,
                            start_col=match.start(),
                            end_col=match.end(),
                        ),
                        original_code=line.strip(),
                        severity=rule.severity,
                        suggested_fix=rule.suggested_fix,
                        metadata=rule.metadata,
                    )

    def match_file(
        self, file_path: Path
    ) -> Generator[DeprecatedPattern, None, None]:
        """
        Match patterns against a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Yields:
            DeprecatedPattern for each match found
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            yield from self.match(source, file_path)
        except Exception as e:
            yield DeprecatedPattern(
                pattern_id="file_error",
                pattern_type="file_error",
                description=f"Error reading file: {str(e)}",
                location=CodeLocation(file_path=file_path, start_line=1, end_line=1),
                original_code="",
                severity="error",
            )

    def get_rules_by_type(self, pattern_type: str) -> list[PatternRule]:
        """Get all rules matching a pattern type."""
        return [r for r in self.rules if r.pattern_type == pattern_type]

    def get_migration_rules(self, migration_type: str) -> list[PatternRule]:
        """Get rules applicable to a specific migration type."""
        if migration_type == "py2to3":
            # Return Python 2 specific patterns
            py2_types = {
                "print_statement", "except_comma_syntax", "backtick_repr",
                "octal_literal", "ur_string_prefix", "xrange_usage",
                "raw_input_usage", "unicode_usage", "long_usage"
            }
            return [r for r in self.rules if r.pattern_type in py2_types]
        
        elif migration_type == "flask_to_fastapi":
            # Return Flask specific patterns
            flask_types = {
                "flask_run", "flask_config", "flask_secret_key",
                "flask_before_request", "flask_after_request", "flask_route_decorator"
            }
            return [r for r in self.rules if r.pattern_type in flask_types]
        
        return []
