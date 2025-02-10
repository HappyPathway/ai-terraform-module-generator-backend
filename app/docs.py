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
            "dependencies": [],
            "resources": []
        }
        
        # Read variables.tf for inputs
        vars_file = module_path / "variables.tf"
        if vars_file.exists():
            docs["inputs"] = DocGenerator._parse_variables(vars_file)
            
        # Read outputs.tf for outputs
        outputs_file = module_path / "outputs.tf"
        if outputs_file.exists():
            docs["outputs"] = DocGenerator._parse_outputs(outputs_file)
            
        # Read README.md for general documentation
        readme_file = module_path / "README.md"
        if readme_file.exists():
            docs["description"] = DocGenerator._parse_readme(readme_file)
            
        return docs
    
    @staticmethod
    def _parse_variables(file_path: Path) -> list:
        """Parse variables from variables.tf"""
        # Simple parser for demo purposes
        return [{"name": "parsed_from_variables.tf"}]
    
    @staticmethod
    def _parse_outputs(file_path: Path) -> list:
        """Parse outputs from outputs.tf"""
        # Simple parser for demo purposes
        return [{"name": "parsed_from_outputs.tf"}]
    
    @staticmethod
    def _parse_readme(file_path: Path) -> str:
        """Parse description from README.md"""
        try:
            return file_path.read_text()
        except:
            return "No description available"

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
