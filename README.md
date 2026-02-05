# DevAssist - Multi-Agent Code Migration Tool

[![CI](https://github.com/your-org/devassist/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/devassist/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DevAssist** is an enterprise-grade multi-agent system for automated code migration across repositories. It uses AI-powered agents to identify deprecated code patterns, rewrite them following best practices, and validate changes through automated testing.

## 🚀 Features

- **Multi-Agent Architecture**: Three specialized AI agents work together:
  - **Planner Agent**: Identifies deprecated code patterns using AST analysis and LLM reasoning
  - **Coder Agent**: Rewrites code following migration rules and style guides
  - **Tester Agent**: Generates and runs unit tests to validate changes

- **Supported Migrations**:
  - Python 2 → Python 3
  - Flask → FastAPI

- **Enterprise Ready**:
  - Automated pull request generation via GitHub API
  - Dockerized testing environments
  - CI/CD integration with GitHub Actions
  - MCP integration for company style guides

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Installation

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for containerized testing)
- OpenAI API key

### Install from PyPI

```bash
pip install devassist
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/devassist.git
cd devassist

# Install in development mode
pip install -e ".[dev]"
```

### Docker Installation

```bash
# Build the Docker image
docker build -t devassist -f docker/Dockerfile .

# Run with Docker
docker run -it devassist --help
```

## 🚀 Quick Start

### 1. Initialize Configuration

```bash
devassist init
```

This creates a `.env.example` file. Copy it to `.env` and add your credentials:

```bash
cp .env.example .env
# Edit .env with your OpenAI API key and GitHub token
```

### 2. Analyze a Repository

```bash
devassist analyze https://github.com/user/legacy-python2-project --type py2to3
```

### 3. Run Migration

```bash
devassist migrate https://github.com/user/legacy-python2-project --type py2to3
```

### 4. Review and Merge PR

The tool automatically creates a pull request with all changes. Review the changes and merge when ready.

## � Web Interface

DevAssist includes a web interface for easy code migration without using the CLI.

### Starting the Web Interface

```bash
# Start the API server
uvicorn devassist.api.main:app --host 0.0.0.0 --port 8000

# In a separate terminal, start the frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to use the web interface.

### Using Docker Compose

```bash
cd docker
docker-compose up api frontend
```

The frontend will be available at `http://localhost:3001` and the API at `http://localhost:8000`.

### Web Interface Features

1. **Upload**: Drag and drop your zipped codebase (downloaded from GitHub)
2. **Select Migration Type**: Choose Python 2→3 or Flask→FastAPI
3. **Process**: Watch real-time progress as the AI agents migrate your code
4. **Download**: Get your migrated codebase as a ZIP file

## 🏗️ Architecture


```
┌─────────────────────────────────────────────────────────────────┐
│                        DevAssist Workflow                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │   Git    │───▶│   AST    │───▶│  Multi-  │───▶│   Pull   │ │
│   │  Clone   │    │ Parsing  │    │  Agent   │    │ Request  │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                         │                        │
│                         ┌───────────────┼───────────────┐       │
│                         ▼               ▼               ▼       │
│                   ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│                   │ Planner  │───▶│  Coder   │───▶│  Tester  │ │
│                   │  Agent   │    │  Agent   │    │  Agent   │ │
│                   └──────────┘    └──────────┘    └──────────┘ │
│                   Identifies      Rewrites         Validates    │
│                   patterns        code             changes      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph Workflow

The agents are orchestrated using LangGraph, which provides:
- State management across agents
- Conditional routing based on results
- Automatic retry logic for failed tests
- Checkpointing for long-running migrations

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVASSIST_OPENAI_API_KEY` | OpenAI API key | Required |
| `DEVASSIST_OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `DEVASSIST_GITHUB_TOKEN` | GitHub personal access token | Required for PR creation |
| `DEVASSIST_MIGRATION_TYPE` | Default migration type | `py2to3` |
| `DEVASSIST_TARGET_BRANCH` | Branch for migration PRs | `devassist/migration` |
| `DEVASSIST_AUTO_CREATE_PR` | Auto-create PRs | `true` |
| `DEVASSIST_DOCKER_ENABLED` | Use Docker for testing | `true` |
| `DEVASSIST_MCP_ENABLED` | Enable MCP for style guides | `false` |

### Configuration File

You can also use a `.env` file in your project root:

```env
DEVASSIST_OPENAI_API_KEY=sk-...
DEVASSIST_GITHUB_TOKEN=ghp_...
DEVASSIST_MIGRATION_TYPE=py2to3
```

## 📖 Usage

### Command Line Interface

```bash
# Show help
devassist --help

# Show configuration
devassist config

# Analyze without making changes
devassist analyze https://github.com/user/repo --type py2to3 --output report.json

# Run migration
devassist migrate https://github.com/user/repo --type flask_to_fastapi

# Dry run (analyze only, no changes)
devassist migrate https://github.com/user/repo --dry-run
```

### Python API

```python
from devassist import MigrationWorkflow, Settings

# Configure settings
import os
os.environ["DEVASSIST_OPENAI_API_KEY"] = "your-key"

# Run migration
workflow = MigrationWorkflow()
result = workflow.run(
    repo_url="https://github.com/user/repo",
    migration_type="py2to3"
)

# Check results
if result.success:
    print(f"Migration completed! PR: {result.pr_url}")
else:
    print(f"Migration failed: {result.state.errors}")
```

### Using Individual Agents

```python
from devassist.agents import PlannerAgent, CoderAgent, TesterAgent
from devassist.core.models import MigrationState, MigrationType

# Create initial state
state = MigrationState(
    repo_url="https://github.com/user/repo",
    migration_type=MigrationType.PY2_TO_PY3,
)

# Run individual agents
planner = PlannerAgent()
state = planner.run(state)

print(f"Found {len(state.deprecated_patterns)} patterns")
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/devassist.git
cd devassist

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/devassist --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

### Code Quality

```bash
# Run linter
ruff check src/ tests/

# Run formatter
black src/ tests/

# Run type checker
mypy src/devassist
```

### Docker Development

```bash
# Build all images
docker-compose -f docker/docker-compose.yml build

# Run services
docker-compose -f docker/docker-compose.yml up

# Run tests in Docker
docker-compose -f docker/docker-compose.yml --profile testing run test-runner
```

## 📁 Project Structure

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
│       │   ├── analyzer.py   # Main AST analyzer
│       │   ├── transformers.py # Code transformers
│       │   └── patterns.py   # Pattern matching rules
│       ├── github/           # GitHub API integration
│       │   ├── manager.py    # Repository operations
│       │   └── pr_generator.py # PR content generation
│       ├── mcp/              # MCP server for documentation
│       │   ├── client.py     # MCP client
│       │   └── server.py     # Local MCP server
│       ├── migrations/       # Migration patterns
│       │   ├── py2to3.py     # Python 2→3 migration
│       │   └── flask_to_fastapi.py # Flask→FastAPI migration
│       ├── core/             # Core models and config
│       │   ├── config.py     # Settings management
│       │   └── models.py     # Data models
│       └── cli.py            # Command line interface
├── tests/                    # Unit and integration tests
├── docker/                   # Docker configuration
├── .github/workflows/        # GitHub Actions CI/CD
└── docs/                     # Documentation
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub API integration
- The Python community for excellent migration tooling inspiration

---

**DevAssist** - Automating code migration, one repository at a time. 🚀
