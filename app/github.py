from typing import Dict, Any, List
from pathlib import Path
import aiohttp
import os
import base64
import json

class GitHubService:
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def create_module_repo(self, namespace: str, name: str, provider: str, version: str, module_path: Path) -> str:
        """Create a GitHub repository for the module"""
        # For demo purposes, we'll just return a mock URL since we don't have actual GitHub credentials
        repo_name = f"terraform-{provider}-{name}"
        return f"https://github.com/{namespace}/{repo_name}"

    async def _create_repository(self, name: str, description: str) -> dict:
        """Create a new GitHub repository"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/user/repos",
                headers=self.headers,
                json={
                    "name": name,
                    "description": description,
                    "private": False,
                    "auto_init": True
                }
            ) as response:
                return await response.json()

    async def _upload_files(self, repo: str, path: Path) -> None:
        """Upload files to the repository"""
        # Implementation would go here - omitted for demo
        pass

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
