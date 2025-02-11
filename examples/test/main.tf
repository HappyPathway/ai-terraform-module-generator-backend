terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

module "vpc" {
  source  = "registry.local/HappyPathway/tfvpc/aws"
  version = "1.0.0"
}