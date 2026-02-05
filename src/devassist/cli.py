"""
DevAssist CLI - Command Line Interface for the migration tool.

Provides commands for:
- Running migrations
- Analyzing repositories
- Managing configuration
"""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from devassist import __version__
from devassist.agents.workflow import MigrationWorkflow
from devassist.core.config import get_settings


console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """DevAssist - Multi-Agent Code Migration Tool.
    
    Automatically migrate legacy code across repositories using
    AI-powered multi-agent workflows.
    """
    pass


@main.command()
@click.argument("repo_url")
@click.option(
    "--type", "-t",
    type=click.Choice(["py2to3", "flask_to_fastapi"]),
    default="py2to3",
    help="Type of migration to perform"
)
@click.option(
    "--branch", "-b",
    default="devassist/migration",
    help="Branch name for migration changes"
)
@click.option(
    "--no-pr",
    is_flag=True,
    help="Skip automatic pull request creation"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Analyze without making changes"
)
def migrate(
    repo_url: str,
    type: str,
    branch: str,
    no_pr: bool,
    dry_run: bool
) -> None:
    """Run migration on a repository.
    
    REPO_URL: URL of the Git repository to migrate.
    
    Examples:
    
        devassist migrate https://github.com/user/repo
        
        devassist migrate https://github.com/user/repo --type flask_to_fastapi
    """
    console.print(f"\n[bold blue]DevAssist[/bold blue] v{__version__}")
    console.print(f"Migration type: [cyan]{type}[/cyan]")
    console.print(f"Repository: [cyan]{repo_url}[/cyan]\n")

    if dry_run:
        console.print("[yellow]Dry run mode - no changes will be made[/yellow]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running migration workflow...", total=None)
        
        try:
            workflow = MigrationWorkflow()
            result = workflow.run(repo_url, type)
            
            progress.update(task, completed=True)
            
            # Display results
            _display_results(result)
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            raise click.Abort()


@main.command()
@click.argument("repo_url")
@click.option(
    "--type", "-t",
    type=click.Choice(["py2to3", "flask_to_fastapi"]),
    default="py2to3",
    help="Type of migration to analyze for"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file for analysis report"
)
def analyze(repo_url: str, type: str, output: str | None) -> None:
    """Analyze a repository for migration patterns.
    
    This command analyzes the repository without making any changes,
    providing a report of patterns found and recommended migrations.
    """
    console.print(f"\n[bold blue]DevAssist Analysis[/bold blue]")
    console.print(f"Repository: [cyan]{repo_url}[/cyan]")
    console.print(f"Migration type: [cyan]{type}[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing repository...", total=None)
        
        try:
            # Run analysis only
            from devassist.github import GitHubManager
            from devassist.agents.planner import PlannerAgent
            from devassist.core.models import MigrationState, MigrationType
            
            github = GitHubManager()
            settings = get_settings()
            
            # Clone repo
            repo_path = github.clone_repository(repo_url, settings.work_dir)
            
            # Discover files
            files = list(github.get_repository_files(repo_path, [".py"]))
            
            # Create state
            state = MigrationState(
                repo_url=repo_url,
                repo_path=repo_path,
                migration_type=MigrationType(type),
                files_to_migrate=files,
            )
            
            # Run planner
            planner = PlannerAgent()
            state = planner.run(state)
            
            progress.update(task, completed=True)
            
            # Display analysis
            _display_analysis(state, output)
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            raise click.Abort()


@main.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()
    
    table = Table(title="DevAssist Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Display safe settings (hide sensitive values)
    table.add_row("OpenAI Model", settings.openai_model)
    table.add_row("OpenAI API Key", "***" if settings.openai_api_key else "[red]Not set[/red]")
    table.add_row("GitHub Token", "***" if settings.github_token else "[red]Not set[/red]")
    table.add_row("Migration Type", settings.migration_type)
    table.add_row("Target Branch", settings.target_branch)
    table.add_row("Auto Create PR", str(settings.auto_create_pr))
    table.add_row("Docker Enabled", str(settings.docker_enabled))
    table.add_row("MCP Enabled", str(settings.mcp_enabled))
    table.add_row("Work Directory", settings.work_dir)
    table.add_row("Log Level", settings.log_level)
    
    console.print(table)


@main.command()
def init() -> None:
    """Initialize DevAssist configuration in current directory."""
    import os
    
    env_content = """# DevAssist Configuration
# Copy this file to .env and fill in your values

# OpenAI Configuration
DEVASSIST_OPENAI_API_KEY=your-openai-api-key
DEVASSIST_OPENAI_MODEL=gpt-4-turbo-preview

# GitHub Configuration
DEVASSIST_GITHUB_TOKEN=your-github-token

# Migration Settings
DEVASSIST_MIGRATION_TYPE=py2to3
DEVASSIST_TARGET_BRANCH=devassist/migration
DEVASSIST_AUTO_CREATE_PR=true

# Docker Settings
DEVASSIST_DOCKER_ENABLED=true
DEVASSIST_DOCKER_IMAGE=python:3.11-slim

# MCP Settings (optional)
DEVASSIST_MCP_ENABLED=false
DEVASSIST_MCP_SERVER_URL=http://localhost:3000

# Logging
DEVASSIST_LOG_LEVEL=INFO
"""
    
    env_path = ".env.example"
    if os.path.exists(env_path):
        console.print(f"[yellow]{env_path} already exists[/yellow]")
    else:
        with open(env_path, "w") as f:
            f.write(env_content)
        console.print(f"[green]Created {env_path}[/green]")
        console.print("Copy to .env and fill in your configuration values.")


def _display_results(result) -> None:
    """Display migration results."""
    state = result.state
    
    # Status
    status_color = "green" if result.success else "red"
    console.print(f"\n[bold {status_color}]{'✓ Migration completed' if result.success else '✗ Migration failed'}[/bold {status_color}]")
    
    # Summary table
    table = Table(title="Migration Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    summary = state.get_summary()
    table.add_row("Status", state.status.value)
    table.add_row("Files Processed", str(summary["files_processed"]))
    table.add_row("Patterns Found", str(summary["patterns_found"]))
    table.add_row("Changes Applied", str(summary["changes_applied"]))
    table.add_row("Tests Passed", "✓" if summary["tests_passed"] else "✗")
    table.add_row("Duration", f"{result.duration_seconds:.2f}s")
    
    console.print(table)
    
    # Errors
    if state.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in state.errors:
            console.print(f"  • {error}")
    
    # PR URL
    if hasattr(result, "pr_url") and result.pr_url:
        console.print(f"\n[bold green]Pull Request:[/bold green] {result.pr_url}")


def _display_analysis(state, output: str | None) -> None:
    """Display analysis results."""
    console.print(f"\n[bold]Analysis Results[/bold]")
    console.print(f"Files analyzed: {len(state.files_to_migrate)}")
    console.print(f"Patterns found: {len(state.deprecated_patterns)}\n")
    
    if state.deprecated_patterns:
        # Group by type
        by_type: dict[str, list] = {}
        for pattern in state.deprecated_patterns:
            if pattern.pattern_type not in by_type:
                by_type[pattern.pattern_type] = []
            by_type[pattern.pattern_type].append(pattern)
        
        table = Table(title="Patterns by Type")
        table.add_column("Pattern Type", style="cyan")
        table.add_column("Count", style="white")
        table.add_column("Severity", style="yellow")
        
        for ptype, patterns in sorted(by_type.items(), key=lambda x: -len(x[1])):
            severity = patterns[0].severity if patterns else "unknown"
            table.add_row(ptype, str(len(patterns)), severity)
        
        console.print(table)
        
        # Save to file if requested
        if output:
            import json
            report = {
                "repository": state.repo_url,
                "migration_type": state.migration_type.value,
                "files_analyzed": len(state.files_to_migrate),
                "patterns_found": len(state.deprecated_patterns),
                "patterns_by_type": {k: len(v) for k, v in by_type.items()},
                "patterns": [
                    {
                        "type": p.pattern_type,
                        "file": str(p.location.file_path),
                        "line": p.location.start_line,
                        "severity": p.severity,
                        "description": p.description,
                    }
                    for p in state.deprecated_patterns
                ]
            }
            with open(output, "w") as f:
                json.dump(report, f, indent=2)
            console.print(f"\n[green]Report saved to {output}[/green]")
    else:
        console.print("[green]No migration patterns found![/green]")


if __name__ == "__main__":
    main()
