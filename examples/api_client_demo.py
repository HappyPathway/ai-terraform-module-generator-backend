#!/usr/bin/env python3
from app.client import TerraformModuleClient
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize the client
    client = TerraformModuleClient(base_url="http://localhost:8000")
    
    try:
        # Test API discovery
        logger.info("Testing API discovery...")
        discovery = client.discover_endpoints()
        logger.info(f"Available endpoints: {discovery}")

        # Search for modules
        logger.info("\nSearching for AWS modules...")
        search_results = client.search_modules("aws", filters={"provider": "aws"})
        logger.info(f"Search results: {search_results}")

        # Example of how to use other endpoints
        try:
            # Get module versions (this might fail if no modules exist yet)
            logger.info("\nTrying to list versions for a module...")
            versions = client.list_versions("example", "test-module", "aws")
            logger.info(f"Module versions: {versions}")
        except Exception as e:
            logger.warning(f"Could not get module versions (this is expected if no modules exist): {e}")

        # Get module stats (this might fail if no modules exist yet)
        try:
            logger.info("\nTrying to get module stats...")
            stats = client.get_module_stats("example", "test-module", "aws")
            logger.info(f"Module stats: {stats}")
        except Exception as e:
            logger.warning(f"Could not get module stats (this is expected if no modules exist): {e}")

    except Exception as e:
        logger.error(f"Error during API testing: {e}")
        raise

if __name__ == "__main__":
    # Wait a few seconds for services to be ready
    logger.info("Waiting for services to be ready...")
    time.sleep(5)
    main()