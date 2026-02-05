"""
GitHub Manager - Core GitHub API integration.

Handles repository operations including cloning, branching,
committing, and pull request creation.
"""

import os
from pathlib import Path
from typing import Generator
import git
from github import Github, GithubException

from devassist.core.config import get_settings


class GitHubManager:
    """
    Manages GitHub repository operations.
    
    Provides methods for:
    - Cloning repositories
    - Creating and switching branches
    - Committing changes
    - Creating pull requests
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.github_token
        self.base_url = settings.github_base_url
        self._github: Github | None = None

    @property
    def github(self) -> Github:
        """Lazy initialization of GitHub client."""
        if self._github is None:
            if self.token:
                self._github = Github(self.token, base_url=self.base_url)
            else:
                self._github = Github()  # Anonymous access
        return self._github

    def clone_repository(self, repo_url: str, work_dir: str) -> Path:
        """
        Clone a repository to the work directory.
        
        Args:
            repo_url: URL of the repository to clone
            work_dir: Directory to clone into
            
        Returns:
            Path to the cloned repository
        """
        # Extract repo name from URL
        repo_name = self._extract_repo_name(repo_url)
        clone_path = Path(work_dir) / repo_name
        
        # Remove existing directory if present
        if clone_path.exists():
            import shutil
            shutil.rmtree(clone_path)
        
        # Clone the repository
        clone_url = self._get_authenticated_url(repo_url)
        git.Repo.clone_from(clone_url, clone_path)
        
        return clone_path

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        # Handle both HTTPS and SSH URLs
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        
        parts = repo_url.rstrip("/").split("/")
        return parts[-1]

    def _get_authenticated_url(self, repo_url: str) -> str:
        """Get authenticated URL for cloning."""
        if not self.token:
            return repo_url
        
        # Add token to HTTPS URL
        if repo_url.startswith("https://"):
            # https://github.com/owner/repo -> https://token@github.com/owner/repo
            return repo_url.replace("https://", f"https://{self.token}@")
        
        return repo_url

    def create_branch(self, repo_path: Path, branch_name: str) -> None:
        """
        Create and checkout a new branch.
        
        Args:
            repo_path: Path to the repository
            branch_name: Name of the branch to create
        """
        repo = git.Repo(repo_path)
        
        # Create branch from current HEAD
        if branch_name not in repo.heads:
            repo.create_head(branch_name)
        
        # Checkout the branch
        repo.heads[branch_name].checkout()

    def commit_changes(
        self, repo_path: Path, message: str, author_name: str = "DevAssist",
        author_email: str = "devassist@example.com"
    ) -> str:
        """
        Commit all changes in the repository.
        
        Args:
            repo_path: Path to the repository
            message: Commit message
            author_name: Name of the commit author
            author_email: Email of the commit author
            
        Returns:
            Commit SHA
        """
        repo = git.Repo(repo_path)
        
        # Add all changes
        repo.git.add(A=True)
        
        # Check if there are changes to commit
        if not repo.is_dirty() and not repo.untracked_files:
            return ""
        
        # Configure author
        repo.config_writer().set_value("user", "name", author_name).release()
        repo.config_writer().set_value("user", "email", author_email).release()
        
        # Commit
        commit = repo.index.commit(message)
        return commit.hexsha

    def push_branch(self, repo_path: Path, branch_name: str) -> None:
        """
        Push a branch to the remote.
        
        Args:
            repo_path: Path to the repository
            branch_name: Name of the branch to push
        """
        repo = git.Repo(repo_path)
        
        # Push to origin
        origin = repo.remote("origin")
        origin.push(branch_name, set_upstream=True)

    def create_pull_request(
        self, repo_path: Path, branch_name: str, title: str, body: str,
        base_branch: str = "main"
    ) -> str:
        """
        Create a pull request on GitHub.
        
        Args:
            repo_path: Path to the repository
            branch_name: Name of the branch with changes
            title: PR title
            body: PR description
            base_branch: Branch to merge into
            
        Returns:
            URL of the created pull request
        """
        # Get repository info from remote
        repo = git.Repo(repo_path)
        remote_url = repo.remote("origin").url
        owner, repo_name = self._parse_remote_url(remote_url)
        
        # Commit and push changes
        self.commit_changes(
            repo_path,
            f"[DevAssist] Migration changes\n\n{title}"
        )
        self.push_branch(repo_path, branch_name)
        
        # Create PR via GitHub API
        try:
            gh_repo = self.github.get_repo(f"{owner}/{repo_name}")
            pr = gh_repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=base_branch
            )
            return pr.html_url
        except GithubException as e:
            raise RuntimeError(f"Failed to create pull request: {e}")

    def _parse_remote_url(self, remote_url: str) -> tuple[str, str]:
        """Parse owner and repo name from remote URL."""
        # Handle HTTPS URLs
        if remote_url.startswith("https://"):
            # https://github.com/owner/repo.git
            parts = remote_url.rstrip(".git").split("/")
            return parts[-2], parts[-1]
        
        # Handle SSH URLs
        if remote_url.startswith("git@"):
            # git@github.com:owner/repo.git
            path = remote_url.split(":")[1].rstrip(".git")
            parts = path.split("/")
            return parts[0], parts[1]
        
        raise ValueError(f"Cannot parse remote URL: {remote_url}")

    def get_repository_files(
        self, repo_path: Path, extensions: list[str] | None = None
    ) -> Generator[Path, None, None]:
        """
        Get all files in the repository matching the given extensions.
        
        Args:
            repo_path: Path to the repository
            extensions: List of file extensions to include (e.g., ['.py'])
            
        Yields:
            Path objects for matching files
        """
        if extensions is None:
            extensions = [".py"]
        
        repo = git.Repo(repo_path)
        
        # Get all tracked files
        for item in repo.tree().traverse():
            if item.type == "blob":
                file_path = repo_path / item.path
                if any(str(file_path).endswith(ext) for ext in extensions):
                    yield file_path

    def get_file_diff(
        self, repo_path: Path, file_path: Path
    ) -> str:
        """
        Get the diff for a specific file.
        
        Args:
            repo_path: Path to the repository
            file_path: Path to the file
            
        Returns:
            Git diff string
        """
        repo = git.Repo(repo_path)
        relative_path = file_path.relative_to(repo_path)
        return repo.git.diff(str(relative_path))

    def get_all_diffs(self, repo_path: Path) -> str:
        """
        Get all uncommitted diffs in the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Combined diff string
        """
        repo = git.Repo(repo_path)
        return repo.git.diff()

    def reset_changes(self, repo_path: Path) -> None:
        """
        Reset all uncommitted changes.
        
        Args:
            repo_path: Path to the repository
        """
        repo = git.Repo(repo_path)
        repo.git.checkout("--", ".")
        repo.git.clean("-fd")

    def get_repo_info(self, owner: str, repo_name: str) -> dict:
        """
        Get information about a repository.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Dictionary with repository information
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
            }
        except GithubException as e:
            raise RuntimeError(f"Failed to get repository info: {e}")
