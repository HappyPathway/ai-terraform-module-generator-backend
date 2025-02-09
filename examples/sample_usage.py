from app.client import TerraformModuleClient
import logging
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize the client
    client = TerraformModuleClient(
        base_url="http://localhost:8000",
        token=os.getenv("TERRAFORM_MODULE_TOKEN")
    )
    
    try:
        # 1. Check API endpoints
        logger.info("Checking API endpoints...")
        endpoints = client.discover_endpoints()
        logger.info(f"Available endpoints: {endpoints}")

        # 2. Search for modules
        logger.info("\nSearching for AWS modules...")
        search_results = client.search_modules(
            query="aws",
            filters={"provider": "aws"}
        )
        logger.info(f"Search results: {search_results}")

        # 3. List versions for a specific module
        # Note: Replace with actual namespace/name/provider when you have modules
        logger.info("\nListing versions for a module...")
        try:
            versions = client.list_versions(
                namespace="example",
                name="vpc",
                provider="aws"
            )
            logger.info(f"Module versions: {versions}")
        except Exception as e:
            logger.warning(f"Could not list versions: {e}")

        # 4. Get module statistics
        logger.info("\nGetting module statistics...")
        try:
            stats = client.get_module_stats(
                namespace="example",
                name="vpc",
                provider="aws"
            )
            logger.info(f"Module statistics: {stats}")
        except Exception as e:
            logger.warning(f"Could not get stats: {e}")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()