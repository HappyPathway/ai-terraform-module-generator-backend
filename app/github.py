from typing import Dict, Any, List
from github import Github
from pathlib import Path
import os
import base64
import json

class GitHubService:
    def __init__(self, token: str):
        self.github = Github(token)

    async def create_module_repo(
        self,
        namespace: str,
        name: str,
        provider: str,
        version: str,
        module_path: Path
    ) -> str:
        repo_name = f"terraform-{provider}-{name}"
        org = self.github.get_organization(namespace)
        repo = org.create_repo(
            repo_name,
            description=f"Terraform module for {name} using {provider}",
            has_issues=True,
            has_wiki=True,
            auto_init=True
        )
        
        # Upload module files
        for file_path in module_path.rglob('*'):
            if file_path.is_file():
                repo.create_file(
                    str(file_path.relative_to(module_path)),
                    f"Initial commit for version {version}",
                    file_path.read_bytes()
                )
        
        return repo.html_url

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def get_terraform_discovery(repo_url: str) -> Dict[str, Any]:
    """
    Get Terraform module discovery information from a GitHub repository
    Returns module metadata if found, otherwise raises exception
    """
    try:
        g = Github(GITHUB_TOKEN)
        
        # Extract owner and repo from URL
        # Example: https://github.com/owner/repo
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Look for module metadata in common locations
        metadata_paths = [
            "module.json",
            "terraform.json",
            ".terraform.json"
        ]
        
        for path in metadata_paths:
            try:
                content = repo.get_contents(path)
                if content:
                    content_str = base64.b64decode(content.content).decode('utf-8')
                    return json.loads(content_str)
            except:
                continue
                
        # If no metadata file found, try to infer from repository
        return {
            "name": repo_name,
            "namespace": owner,
            "provider": "github",
            "version": "0.1.0",  # Default version
            "description": repo.description or "",
            "source": repo_url
        }
        
    except Exception as e:
        raise Exception(f"Error getting module discovery info: {str(e)}")
