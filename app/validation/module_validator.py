from pathlib import Path
import zipfile

class ModuleValidator:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def validate(self) -> bool:
        if not zipfile.is_zipfile(self.file_path):
            return False
            
        required_files = ['main.tf', 'variables.tf', 'outputs.tf']
        with zipfile.ZipFile(self.file_path) as zip_file:
            file_list = zip_file.namelist()
            return all(any(f.endswith(req) for f in file_list) for req in required_files)
