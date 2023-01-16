import subprocess
from typing import Tuple, Dict
from abc import ABC, abstractmethod

from network import Address, NetworkOptions
from storage import BaseStorage
from client import SocketClient


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


class ReportCommand(Command):
    def __init__(self, storage: BaseStorage, report: str, options: NetworkOptions) -> None:
        self.storage, self.report, self.options = storage, report, options

    def execute(self) -> str:
        parent = self.storage.get_parent()
        client = SocketClient(self.options)
        client.change_destination(parent)
        client.send_message(str(self))

    def __str__(self) -> str:
        return "REPORT {}".format(self.report)


class InitCommand(Command):
    def __init__(self, storage: BaseStorage, child: Address) -> None:
        self.storage = storage
        self.child = child

    def execute(self) -> str:
        if self.child in self.storage.get_childs():
            return "ALREADY"

        self.storage.add_child(self.child)
        return "OK"
    
    def __str__(self) -> str:
        return "INIT"

class ChildCommand(Command):
    """ Randomly selects a child host in the storage to redirect. Then adds a child to self storage"""
    def __init__(
        self, storage: BaseStorage, child: Address, options: NetworkOptions) -> None:
        self.storage, self.child, self.options = storage, child, options

    def execute(self) -> str:
        client = SocketClient(self.options)
        for child in self.storage.get_childs():
            client.change_destination(child)
            client.send_message(str(self))
        
        self.storage.add_child(self.child)
        return "OK"

    def __str__(self) -> str:
        return "ADD_CHILD:{}".format(str(self.child))
