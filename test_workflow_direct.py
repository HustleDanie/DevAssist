"""Direct test of the migration workflow without the API server."""
import sys
sys.path.insert(0, 'src')

from devassist.agents.workflow import MigrationWorkflow

print("Testing direct workflow execution...")

try:
    print("\n1. Creating workflow...")
    workflow = MigrationWorkflow()
    
    print("\n2. Running migration...")
    result = workflow.run(
        repo_url="https://github.com/HustleDanie/legacy-python2-app",
        migration_type="py2to3"
    )
    
    print(f"\n3. Result: success={result.success}")
    print(f"   Summary: {result.summary}")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    
    print("\n4. State details:")
    state = result.state
    print(f"   Files to migrate: {len(state.files_to_migrate) if state.files_to_migrate else 0}")
    print(f"   Patterns found: {len(state.deprecated_patterns) if state.deprecated_patterns else 0}")
    print(f"   Changes applied: {len(state.applied_changes) if state.applied_changes else 0}")
    print(f"   Tests passed: {state.tests_passed}")
    
    print("\n5. Test Results:")
    for tr in (state.test_results or []):
        print(f"   - {tr.test_name}: passed={tr.passed}")
        if not tr.passed:
            if tr.error_message:
                print(f"     Error: {tr.error_message[:500]}")
            if tr.stderr:
                print(f"     Stderr: {tr.stderr[:500]}")
            if tr.stdout:
                print(f"     Stdout: {tr.stdout[:500]}")
    
    print("\n6. Messages:")
    for msg in state.messages[:10]:
        if isinstance(msg, dict):
            print(f"   [{msg.get('role', 'system')}] {msg.get('content', '')}")
        else:
            print(f"   {msg}")

except Exception as e:
    import traceback
    print(f"\nERROR: {type(e).__name__}: {e}")
    print("\nTraceback:")
    traceback.print_exc()

print("\nDone!")
