# AWS VPC Terraform Module

This Terraform module creates a VPC with public subnets in AWS.

## Usage

```hcl
module "vpc" {
  source = "example/vpc/aws"

  vpc_name           = "my-vpc"
  vpc_cidr          = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
  
  tags = {
    Environment = "dev"
    Team        = "infrastructure"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| vpc_name | Name tag for the VPC | `string` | n/a | yes |
| vpc_cidr | CIDR block for the VPC | `string` | `"10.0.0.0/16"` | no |
| enable_dns_hostnames | Enable DNS hostnames in the VPC | `bool` | `true` | no |
| enable_dns_support | Enable DNS support in the VPC | `bool` | `true` | no |
| public_subnets | List of public subnet CIDR blocks | `list(string)` | `["10.0.1.0/24", "10.0.2.0/24"]` | no |
| availability_zones | List of availability zones | `list(string)` | n/a | yes |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | The ID of the VPC |
| vpc_arn | The ARN of the VPC |
| public_subnet_ids | List of public subnet IDs |
| vpc_cidr_block | The CIDR block of the VPC |