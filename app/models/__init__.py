from .models import Module, DBModuleVersion

class ModuleResponse(Module):
    class Config:
        orm_mode = True

__all__ = ['Module', 'ModuleResponse', 'DBModuleVersion']