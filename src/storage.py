from abc import ABC, abstractmethod
from typing import Set
from network import Address
import hashlib
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
    
    @abstractmethod
    def is_command_hashed(self, command) -> None:
        pass

    @abstractmethod
    def add_hash_command(self, command) -> None:
        pass


class InMemoryStorage(BaseStorage):
    """Lives while the server is running. Not resistant to system restart"""
    def __init__(self, parent: Address = None, childs: Set[Address] = None) -> None:
        super(InMemoryStorage, self).__init__()
        self.hash_commands = set()
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

    def is_command_hashed(self, command) -> bool:
        hash = hashlib.md5(str(command).encode('utf-8')).hexdigest()
        return hash in self.hash_commands

    def add_hash_command(self, command) -> None:
        hash = hashlib.md5(str(command).encode('utf-8')).hexdigest()
        self.hash_commands.add(hash)


class FileStorage(BaseStorage):
    """ We need something like this, because if the computer 
        is turned off, then all childs and parents bots will be lost """
    pass
