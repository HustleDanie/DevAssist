# DevAssist - Multi-Agent Code Migration Tool

## Project Overview
DevAssist is an enterprise-grade multi-agent system for automated code migration (Python 2→3, Flask→FastAPI) across repositories.

## Architecture
- **Git Clone** → **AST Parsing** → **Multi-Agent Refactoring** → **Pull Request Generation**

## Tech Stack
- Python 3.11+ (Advanced: Generators/Iterators, AST)
- LangChain/LangGraph for agent orchestration
- GitHub API for automated PRs
- Docker for containerized testing
- MCP (Model Context Protocol) for documentation context

## Project Structure
```
DevAssist/
├── src/
│   └── devassist/
│       ├── agents/           # LangGraph multi-agent system
│       │   ├── planner.py    # Agent 1: Identifies deprecated code
│       │   ├── coder.py      # Agent 2: Rewrites code
│       │   ├── tester.py     # Agent 3: Writes/runs unit tests
│       │   └── workflow.py   # LangGraph workflow orchestration
│       ├── ast_parser/       # AST analysis and transformation
│       ├── github/           # GitHub API integration
│       ├── mcp/              # MCP server for documentation
│       └── migrations/       # Migration patterns (Py2→3, Flask→FastAPI)
├── tests/                    # Unit and integration tests
├── docker/                   # Dockerfile and compose configs
├── .github/workflows/        # GitHub Actions CI/CD
└── docs/                     # Documentation
```

## Development Guidelines
- Use type hints throughout the codebase
- Follow PEP 8 style guidelines
- Write unit tests for all agent behaviors
- Use generators/iterators for large file processing
- Document all migration patterns

## Commands
- `pip install -e .` - Install in development mode
- `pytest` - Run tests
- `python -m devassist migrate <repo_url>` - Run migration
