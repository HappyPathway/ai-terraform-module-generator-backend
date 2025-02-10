provider "azurerm" {
  features {}
}

module "test_storage" {
  source = "../azure-storage"

  resource_group_name  = "test-resources"
  storage_account_name = "teststorageaccount"
  location            = "eastus"
  container_names     = ["test-container-1", "test-container-2"]
  
  tags = {
    Environment = "test"
    Project     = "module-testing"
  }
}