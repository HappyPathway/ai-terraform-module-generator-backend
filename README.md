# AI Terraform Module Generator - Backend Service API Documentation

## Overview
The AI Terraform Module Generator backend service implements the Terraform Registry Protocol and provides additional endpoints for module management and search. This document outlines the available API endpoints and their contracts.

## Terraform Registry API Endpoints

### 1. Registry Discovery
- **Endpoint:** `/.well-known/terraform.json`
- **Method:** GET
- **Description:** Provides the base URL for the Terraform Registry API.
- **Response:**
  ```json
  {
    "modules.v1": "/v1/modules/"
  }
  ```

### 2. List Module Versions
- **Endpoint:** `/v1/modules/{namespace}/{name}/{provider}/versions`
- **Method:** GET
- **Description:** Lists available versions for a module.
- **Response:**
  ```json
  {
    "modules": [
      {
        "versions": [
          {
            "version": "1.0.0",
            "protocols": ["5.0"],
            "platforms": [
              {
                "os": "linux",
                "arch": "amd64"
              }
            ]
          }
        ]
      }
    ]
  }
  ```

### 3. Get Module Download URL
- **Endpoint:** `/v1/modules/{namespace}/{name}/{provider}/{version}/download`
- **Method:** GET
- **Description:** Retrieves the download URL for a specific module version.
- **Response:**
  ```json
  {
    "source": "https://example.com/module.zip"
  }
  ```

### 4. Download Module Source
- **Endpoint:** `/v1/modules/{namespace}/{name}/{provider}/{version}/source`
- **Method:** GET
- **Description:** Downloads the source code for a specific module version.
- **Response:** Binary data (ZIP file)

## Additional API Endpoints

### 1. Search Modules
- **Endpoint:** `/v1/modules/search`
- **Method:** GET
- **Description:** Searches for modules with optional filtering.
- **Query Parameters:**
  - `q` (string): Search query
  - `provider` (string, optional): Filter by provider
  - `namespace` (string, optional): Filter by namespace
  - `limit` (int, optional): Number of results to return (default: 10)
  - `offset` (int, optional): Offset for pagination (default: 0)
- **Response:**
  ```json
  {
    "modules": [
      {
        "id": "module-id",
        "owner": "module-owner",
        "namespace": "module-namespace",
        "name": "module-name",
        "version": "latest-version",
        "provider": "module-provider",
        "description": "module-description",
        "source": "module-source-url",
        "published_at": "publish-date",
        "downloads": 123,
        "verified": true
      }
    ]
  }
  ```

### 2. List Module Dependencies
- **Endpoint:** `/v1/modules/{namespace}/{name}/{provider}/{version}/dependencies`
- **Method:** GET
- **Description:** Lists dependencies for a specific module version.
- **Response:**
  ```json
  {
    "dependencies": [
      {
        "source": "dependency-source",
        "version": "dependency-version"
      }
    ]
  }
  ```

### 3. Get Module Statistics
- **Endpoint:** `/v1/modules/{namespace}/{name}/{provider}/stats`
- **Method:** GET
- **Description:** Retrieves statistics for a module.
- **Response:**
  ```json
  {
    "downloads": 1234,
    "stars": 56,
    "forks": 7
  }
  ```

## Rate Limiting
The API implements rate limiting of 100 requests per minute per IP address.

## Authentication
The API uses JWT-based authentication for protected endpoints. Include the JWT token in the `Authorization` header as follows:
```
Authorization: Bearer <token>
```

## Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export GITHUB_TOKEN=your_token
```

3. Run the development server:
```bash
uvicorn app.main:app --reload
