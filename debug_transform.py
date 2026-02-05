"""Debug the transformation of all test files."""
import sys
sys.path.insert(0, 'src')
import os
import ast

from devassist.ast_parser.transformers import Py2to3Transformer

t = Py2to3Transformer()

test_dir = "test-repos/legacy-python2-app"
for filename in os.listdir(test_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(test_dir, filename)
        with open(filepath, "r") as f:
            code = f.read()
        
        result, changes = t.transform(code)
        
        # Check for syntax errors
        try:
            ast.parse(result)
            status = "OK"
        except SyntaxError as e:
            status = f"SYNTAX ERROR at line {e.lineno}: {e.msg}"
        
        print(f"{filename}: {status} ({len(changes)} changes)")
