# ai-terraform-module-generator-backend
FastAPI backend for the AI Terraform Module Generator

## Terraform Registry API Implementation

This backend implements the necessary Terraform Registry Protocol endpoints to serve as a private registry. The following endpoints are supported:

- `/.well-known/terraform.json` - Registry discovery protocol
- `/v1/modules/{namespace}/{name}/{provider}/versions` - List available versions
- `/v1/modules/{namespace}/{name}/{provider}/{version}/download` - Download source code

For more information about the Terraform Registry Protocol, see the [official documentation](https://www.terraform.io/docs/internals/provider-registry-protocol.html).

## Additional API Endpoints

### Module Search and Statistics
- `/v1/modules/search` - Search for modules with filtering
- `/v1/modules/{namespace}/{name}/{provider}/stats` - Get module statistics
- `/v1/modules/{namespace}/{name}/{provider}/{version}/dependencies` - List module dependencies

### Rate Limiting
The API implements rate limiting of 100 requests per minute per IP address.

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
