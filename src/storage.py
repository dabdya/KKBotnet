from abc import ABC, abstractmethod
from typing import Set, Union
from network import Address

from pathlib import Path

class BaseStorage(ABC):
    """Storage interface"""
    @abstractmethod
    def get_childs(self) -> Set[Address]:
        pass

    @abstractmethod
    def add_child(self, child: Address) -> None:
        pass

    @abstractmethod
    def delete_child(self, child: Address) -> None:
        pass

    @abstractmethod
    def get_parent(self) -> Address:
        pass

    @abstractmethod
    def change_parent(self, parent: Address) -> None:
        pass


class InMemoryStorage(BaseStorage):
    """Lives while the server is running. Not resistant to system restart"""
    def __init__(self, parent: Address = None, childs: Set[Address] = None) -> None:
        super(InMemoryStorage, self).__init__()
        self.childs, self.parent = childs, parent
        if not self.childs:
            self.childs = set()
    
    def get_childs(self) -> Set[Address]:
        return self.childs
    
    def get_parent(self) -> Address:
        return self.parent

    def delete_child(self, child: Address) -> None:
        self.childs.remove(child)
    
    def add_child(self, child: Address) -> None:
        self.childs.add(child)

    def change_parent(self, parent: Address) -> None:
        self.parent = parent


class FileStorage(BaseStorage):
    """ We need something like this, because if the computer 
        is turned off, then all childs and parents bots will be lost """
    pass
