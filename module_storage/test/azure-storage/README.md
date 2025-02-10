# Azure Storage Account Terraform Module

This Terraform module creates an Azure Storage Account with optional blob containers.

## Usage

```hcl
module "storage" {
  source = "example/storage/azure"

  resource_group_name  = "my-resources"
  storage_account_name = "mystorageaccount"
  location            = "eastus"
  container_names     = ["container1", "container2"]
  
  tags = {
    Environment = "prod"
    Team        = "data"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| azurerm | ~> 3.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| resource_group_name | Name of the resource group | `string` | n/a | yes |
| storage_account_name | Name of the storage account | `string` | n/a | yes |
| location | Azure region where resources will be created | `string` | `"eastus"` | no |
| account_tier | Performance tier of the storage account | `string` | `"Standard"` | no |
| replication_type | Type of replication for the storage account | `string` | `"LRS"` | no |
| container_names | List of container names to create | `list(string)` | `[]` | no |
| container_access_type | Access type for containers | `string` | `"private"` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| storage_account_id | The ID of the storage account |
| storage_account_name | The name of the storage account |
| primary_access_key | The primary access key for the storage account |
| container_ids | The IDs of the storage containers |