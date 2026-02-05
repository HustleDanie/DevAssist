"""
AST Parser module - Abstract Syntax Tree analysis for code migration.

This module provides tools for parsing, analyzing, and transforming Python
code at the AST level to identify and migrate deprecated patterns.
"""

from devassist.ast_parser.analyzer import ASTAnalyzer
from devassist.ast_parser.transformers import (
    Py2to3Transformer,
    FlaskToFastAPITransformer,
)
from devassist.ast_parser.patterns import PatternMatcher

__all__ = [
    "ASTAnalyzer",
    "Py2to3Transformer",
    "FlaskToFastAPITransformer",
    "PatternMatcher",
]
