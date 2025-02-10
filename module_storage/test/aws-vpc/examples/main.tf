provider "aws" {
  region = "us-west-2"
}

module "test_vpc" {
  source = "../aws-vpc"

  vpc_name           = "test-vpc"
  vpc_cidr          = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
  
  tags = {
    Environment = "test"
    Project     = "module-testing"
  }
}