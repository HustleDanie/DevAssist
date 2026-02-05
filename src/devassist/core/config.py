"""Configuration management for DevAssist."""

from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key for LLM calls")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model to use")

    # GitHub Configuration
    github_token: str = Field(default="", description="GitHub personal access token")
    github_base_url: str = Field(
        default="https://api.github.com", description="GitHub API base URL"
    )

    # Migration Configuration
    migration_type: Literal["py2to3", "flask_to_fastapi"] = Field(
        default="py2to3", description="Type of migration to perform"
    )
    target_branch: str = Field(
        default="devassist/migration", description="Branch name for migration PRs"
    )
    auto_create_pr: bool = Field(
        default=True, description="Automatically create pull request after migration"
    )

    # Docker Configuration
    docker_enabled: bool = Field(
        default=False, description="Enable Docker for testing environments"
    )
    docker_image: str = Field(
        default="python:3.11-slim", description="Docker image for testing"
    )

    # MCP Configuration
    mcp_enabled: bool = Field(
        default=False, description="Enable MCP for documentation context"
    )
    mcp_server_url: str = Field(
        default="http://localhost:3000", description="MCP server URL"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )

    # Work Directory
    work_dir: str = Field(
        default=".devassist_work", description="Working directory for cloned repos"
    )

    class Config:
        env_prefix = "DEVASSIST_"
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
