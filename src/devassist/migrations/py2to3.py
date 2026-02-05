"""
Python 2 to Python 3 Migration - Specific migration patterns and rules.

This module provides comprehensive migration support for converting
Python 2 code to Python 3, handling syntax changes, library updates,
and behavioral differences.
"""

from dataclasses import dataclass
from typing import Generator

from devassist.ast_parser import ASTAnalyzer, Py2to3Transformer, PatternMatcher
from devassist.core.models import (
    MigrationType,
    DeprecatedPattern,
    CodeChange,
    CodeLocation,
)


@dataclass
class MigrationRule:
    """A specific migration rule for Python 2 to 3."""
    
    name: str
    description: str
    category: str  # syntax, stdlib, behavior
    auto_fix: bool = True


class Py2to3Migration:
    """
    Handles Python 2 to Python 3 migration.
    
    Supported migrations:
    - Print statement to print function
    - xrange to range
    - dict.iteritems/iterkeys/itervalues to items/keys/values
    - Exception syntax changes
    - Unicode handling
    - Module renames
    - Division behavior
    """

    def __init__(self) -> None:
        self.analyzer = ASTAnalyzer()
        self.transformer = Py2to3Transformer()
        self.pattern_matcher = PatternMatcher()
        self.rules = self._build_rules()

    def _build_rules(self) -> list[MigrationRule]:
        """Build the list of migration rules."""
        return [
            MigrationRule(
                name="print_statement",
                description="Convert print statements to print() function",
                category="syntax"
            ),
            MigrationRule(
                name="xrange_to_range",
                description="Replace xrange() with range()",
                category="stdlib"
            ),
            MigrationRule(
                name="dict_iter_methods",
                description="Replace dict.iteritems/iterkeys/itervalues",
                category="stdlib"
            ),
            MigrationRule(
                name="except_syntax",
                description="Convert 'except E, e:' to 'except E as e:'",
                category="syntax"
            ),
            MigrationRule(
                name="unicode_handling",
                description="Update unicode() to str(), handle encoding",
                category="stdlib"
            ),
            MigrationRule(
                name="raw_input",
                description="Replace raw_input() with input()",
                category="stdlib"
            ),
            MigrationRule(
                name="module_renames",
                description="Update renamed standard library modules",
                category="stdlib"
            ),
            MigrationRule(
                name="division",
                description="Handle integer division changes",
                category="behavior"
            ),
            MigrationRule(
                name="long_type",
                description="Replace long() with int()",
                category="stdlib"
            ),
            MigrationRule(
                name="reduce_moved",
                description="Import reduce from functools",
                category="stdlib"
            ),
        ]

    def analyze(self, source: str) -> Generator[DeprecatedPattern, None, None]:
        """
        Analyze source code for Python 2 patterns.
        
        Args:
            source: Python source code
            
        Yields:
            DeprecatedPattern for each issue found
        """
        # Use AST analyzer
        yield from self.analyzer.analyze(source, MigrationType.PY2_TO_PY3)
        
        # Use pattern matcher for regex-based patterns
        yield from self.pattern_matcher.match(source)

    def transform(self, source: str) -> tuple[str, list[CodeChange]]:
        """
        Transform Python 2 source to Python 3.
        
        Args:
            source: Python 2 source code
            
        Returns:
            Tuple of (transformed_code, list_of_changes)
        """
        transformed, changes_list = self.transformer.transform(source)
        
        # Convert change descriptions to CodeChange objects
        changes: list[CodeChange] = []
        for i, change_desc in enumerate(changes_list):
            changes.append(CodeChange(
                change_id=f"py2to3_{i}",
                pattern_id=f"transform_{i}",
                file_path="",
                original_code="",  # Would need AST tracking for exact code
                new_code="",
                start_line=0,
                end_line=0,
                explanation=change_desc,
            ))
        
        return transformed, changes

    def get_futurize_imports(self, source: str) -> list[str]:
        """
        Determine which __future__ imports are needed.
        
        Args:
            source: Source code to analyze
            
        Returns:
            List of recommended __future__ imports
        """
        imports = []
        
        # Check for print statements
        if "print " in source and "print(" not in source:
            imports.append("from __future__ import print_function")
        
        # Check for division
        if "/" in source:
            imports.append("from __future__ import division")
        
        # Always recommend absolute_import for compatibility
        imports.append("from __future__ import absolute_import")
        
        return imports

    def migrate_file(
        self, source: str, apply_fixes: bool = True
    ) -> dict:
        """
        Perform complete migration analysis and optionally apply fixes.
        
        Args:
            source: Source code to migrate
            apply_fixes: Whether to apply automatic fixes
            
        Returns:
            Dictionary with migration results
        """
        # Analyze for patterns
        patterns = list(self.analyze(source))
        
        # Group by category
        by_category: dict[str, list[DeprecatedPattern]] = {}
        for pattern in patterns:
            category = "other"
            for rule in self.rules:
                if rule.name in pattern.pattern_type:
                    category = rule.category
                    break
            
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pattern)
        
        result = {
            "patterns_found": len(patterns),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "patterns": patterns,
        }
        
        if apply_fixes:
            transformed, changes = self.transform(source)
            result["transformed"] = transformed
            result["changes"] = changes
            result["changes_applied"] = len(changes)
        
        return result

    def get_migration_summary(self, patterns: list[DeprecatedPattern]) -> str:
        """
        Generate a human-readable summary of required migrations.
        
        Args:
            patterns: List of patterns found
            
        Returns:
            Summary string
        """
        if not patterns:
            return "No Python 2 patterns found. Code appears to be Python 3 compatible."
        
        lines = [f"Found {len(patterns)} Python 2 patterns that need migration:\n"]
        
        # Count by type
        by_type: dict[str, int] = {}
        for pattern in patterns:
            by_type[pattern.pattern_type] = by_type.get(pattern.pattern_type, 0) + 1
        
        for ptype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  - {ptype}: {count} occurrences")
        
        # Add recommendations
        lines.append("\nRecommended actions:")
        if "print_statement" in by_type:
            lines.append("  1. Add 'from __future__ import print_function' for compatibility")
        lines.append("  2. Run automated transformation")
        lines.append("  3. Review and test all changes")
        
        return "\n".join(lines)
