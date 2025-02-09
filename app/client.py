import requests
from typing import Optional, Dict, Any, List
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerraformModuleClientError(Exception):
    """Base exception for client errors"""
    pass

class TerraformModuleClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token or os.getenv('TERRAFORM_MODULE_TOKEN')
        self.headers = {
            "Authorization": f"Bearer {self.token}" if self.token else ""
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise TerraformModuleClientError(f"API request failed: {e}")

    def discover_endpoints(self) -> Dict[str, Any]:
        """Get registry endpoints following Terraform Registry Protocol."""
        return self._make_request("GET", ".well-known/terraform.json")

    def list_versions(self, namespace: str, name: str, provider: str) -> Dict[str, Any]:
        """List available versions for a module."""
        return self._make_request(
            "GET",
            f"v1/modules/{namespace}/{name}/{provider}/versions"
        )

    def search_modules(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for modules with optional filters."""
        params = {"query": query}
        if filters:
            params.update(filters)
        return self._make_request("GET", "v1/modules/search", params=params)

    def upload_module(self, namespace: str, name: str, provider: str, 
                     version: str, file_path: str) -> Dict[str, Any]:
        """Upload a new module version."""
        with open(file_path, 'rb') as f:
            files = {'file': ('module.zip', f)}
            return self._make_request(
                "POST",
                f"api/modules/{namespace}/{name}/{provider}/{version}/upload",
                files=files
            )

    def get_module_stats(self, namespace: str, name: str, provider: str) -> Dict[str, Any]:
        """Get statistics for a module."""
        return self._make_request(
            "GET",
            f"v1/modules/{namespace}/{name}/{provider}/stats"
        )

    def get_module_dependencies(self, namespace: str, name: str, 
                              provider: str, version: str) -> Dict[str, Any]:
        """Get dependencies for a specific module version."""
        return self._make_request(
            "GET",
            f"v1/modules/{namespace}/{name}/{provider}/{version}/dependencies"
        )

if __name__ == "__main__":
    # Example usage
    client = TerraformModuleClient()
    
    try:
        # Basic discovery
        logger.info("Discovering endpoints...")
        print(client.discover_endpoints())
        
        # Search with filters
        logger.info("\nSearching modules...")
        print(client.search_modules("aws", filters={"provider": "aws", "verified": True}))
    except TerraformModuleClientError as e:
        logger.error(f"Client error: {e}")