import subprocess
from typing import Tuple, Dict
from abc import ABC, abstractmethod

from network import Address
from storage import BaseStorage
from client import NetworkClient


class Command(ABC):
    """Command interface"""
    def __init__(
        self, name: str = "", 
        args: Tuple[str] = tuple(), **kwargs: Dict[str, str]) -> None:

        self.name, self.args = name, args
        for arg_name, arg_value in kwargs.items():
            setattr(self, arg_name, arg_value)

    @abstractmethod
    def execute(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
    

class ConsoleCommand(Command):
    """UNIX shell command executor"""
    def execute(self) -> str:
        input_ = " ".join([self.name, *self.args])
        try:
            output = subprocess.check_output(input_, shell = True).decode()
            return output
        except subprocess.CalledProcessError as err:
            return str(err)

    def __str__(self) -> str:
        return "CONSOLE {}".format(" ".join([self.name, *self.args]))


class ChildCommand(Command):
    """ Randomly selects a child host in the storage to redirect. Then adds a child to self storage"""
    def __init__(
        self, storage: BaseStorage, child: Address, client: NetworkClient) -> None:
        self.storage, self.child, self.client = storage, child, client

    def execute(self) -> str:
        for child in self.storage.get_childs():
            self.client.change_destination(child)
            self.client.send_message(str(self))
        
        self.storage.add_child(self.child)
        return "OK"

    def __str__(self) -> str:
        return "ADD_CHILD:{}".format(str(self.child))
