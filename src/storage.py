from abc import ABC, abstractmethod
from typing import Set
from pathlib import Path
from network import Address

import hashlib, sqlite3 as sql


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
    @staticmethod
    def create_path_if_not_exists(path: Path) -> None:
        path_dirs = Path("/".join(path.parts[:-1]))
        if not path_dirs.exists():
            path_dirs.mkdir(parents = True)
            
    def __init__(self, storage: Path = None) -> None:
        if not storage:
            storage = Path("data/storage.sqlite")
        if not storage.exists():
            FileStorage.create_path_if_not_exists(storage)
        self.conn = sql.connect(storage)

    def create_tables(self) -> None:
        pass
