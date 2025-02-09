import hcl2
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
import os

DOCS_DIR = os.getenv("DOCS_DIR", "./docs")

class DocGenerator:
    @staticmethod
    def generate_module_docs(module_path: Path) -> Dict:
        docs = {
            "inputs": [],
            "outputs": [],
            "resources": []
        }
        
        # Parse variables
        var_file = module_path / "variables.tf"
        if var_file.exists():
            with var_file.open() as f:
                variables = hcl2.load(f)
                for var in variables.get("variable", []):
                    for var_name, var_config in var.items():
                        docs["inputs"].append({
                            "name": var_name,
                            "type": var_config.get("type", "string"),
                            "description": var_config.get("description", ""),
                            "default": var_config.get("default", None)
                        })
        
        # Parse outputs
        out_file = module_path / "outputs.tf"
        if out_file.exists():
            with out_file.open() as f:
                outputs = hcl2.load(f)
                for out in outputs.get("output", []):
                    for out_name, out_config in out.items():
                        docs["outputs"].append({
                            "name": out_name,
                            "description": out_config.get("description", "")
                        })
        
        return docs

async def update_documentation(module_metadata: Dict[str, Any], readme_content: Optional[str] = None) -> str:
    """
    Update module documentation
    Returns the path to the generated documentation
    """
    # Create docs directory if it doesn't exist
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    # Generate documentation path
    doc_path = os.path.join(
        DOCS_DIR,
        f"{module_metadata['namespace']}-{module_metadata['name']}-{module_metadata['provider']}.md"
    )
    
    # Generate documentation content
    content = [
        f"# {module_metadata['name']}",
        "",
        module_metadata.get('description', ''),
        "",
        "## Provider",
        "",
        f"`{module_metadata['provider']}`",
        "",
        "## Version",
        "",
        f"`{module_metadata['version']}`",
        "",
    ]
    
    if readme_content:
        content.extend([
            "## Documentation",
            "",
            readme_content
        ])
    
    # Write documentation
    with open(doc_path, 'w') as f:
        f.write('\n'.join(content))
    
    return doc_path
