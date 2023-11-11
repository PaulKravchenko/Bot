import pickle
import traceback
from pathlib import Path
from typing import Dict

class Serializable:
    def __init__(self, file_name) -> None:
        self.__file_name = file_name
    
    def deserialize(self):
        if Path(self.__file_name).exists():
            with open(self.__file_name, "rb") as file:
                self.data = pickle.load(file)
        return self
    
    def serialize(self):                
        with open(self.__file_name, "wb") as file:
            pickle.dump(self.data, file)              


class SerializationContext:
    def __init__(self,*objects) -> None:
        self.__objects: Dict[str,Serializable] = {type(obj):obj for obj in objects}

    def __enter__(self) -> Dict[str,Serializable]:
        for obj in self.__objects.values():
            obj.deserialize()
        return self.__objects
    
    def __exit__(self, exc_type:type, exc_val, exc_tb):                
        for obj in self.__objects.values():
            obj.serialize()       
        if exc_type:
            tb = '\n'.join(traceback.format_tb(exc_tb))
            print(f"Exception detected\n{exc_type.__name__}: {exc_val}\n{tb}")            
        return True 