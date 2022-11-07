from abc import ABC, abstractmethod
from typing import Set, Union
from network import Address


class BaseStorage(ABC):
    """Storage interface"""
    @abstractmethod
    def get_childs(self) -> Set[Address]:
        pass

    @abstractmethod
    def add_child(self, child: Address) -> None:
        pass

    @abstractmethod
    def get_parents(self) -> Set[Address]:
        pass

    @abstractmethod
    def add_parent(self, parent: Address) -> None:
        pass


class InMemoryStorage(BaseStorage):
    """Lives while the server is running. Not resistant to system restart"""
    def __init__(self, childs: Set[Address] = None, parents: Set[Address] = None) -> None:
        super().__init__()
        self.childs, self.parents = childs, parents
        if not self.childs:
            self.childs = set()
        if not self.parents:
            self.parents = set()
    
    def get_childs(self) -> Set[Address]:
        return self.childs
    
    def get_parents(self) -> Set[Address]:
        return self.parents
    
    def add_child(self, child: Address) -> None:
        self.childs.add(child)

    def add_parent(self, parent: Address) -> None:
        self.parents.add(parent)


class FileStorage(BaseStorage):
    """ We need something like this, because if the computer 
        is turned off, then all childs and parents bots will be lost """
    pass
