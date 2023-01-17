import subprocess, random
from typing import Tuple, Dict, Optional, List
from ipaddress import ip_address

import sys, inspect
from logger import LOG

from network import Address, NetworkOptions
from storage import BaseStorage
from client import SocketClient


class Command:
    """Command interface"""
    def __init__(
        self, hash: str, storage: BaseStorage, options: NetworkOptions, 
        args: Tuple[str] = tuple(), **kwargs: Dict[str, str]) -> None:

        self.storage, self.options = storage, options
        self.hash, self.args = hash, args

        for arg_name, arg_value in kwargs.items():
            setattr(self, arg_name, arg_value)

    def execute(self) -> str:
        raise NotImplementedError()

    def match(self, command: str) -> bool:
        raise NotImplementedError()

    def __str__(self) -> str:
        raise NotImplementedError()
    

class ConsoleCommand(Command):
    """Unix shell command executor"""
    def execute(self) -> str:
        bash_input = " ".join(self.args)
        try:
            output = subprocess.check_output(bash_input, shell = True).decode()
            return output
        except subprocess.CalledProcessError as err:
            return str(err)

    def __str__(self) -> str:
        return "{} CONSOLE {}".format(self.hash, " ".join(self.args))


class ReportCommand(Command):
    """Report command executor"""
    def execute(self) -> str:
        client = SocketClient(self.options)
        client.change_destination(self.storage.get_parent())
        client.send_message(str(self))

    def __str__(self) -> str:
        return "{} REPORT {}".format(self.hash, " ".join(self.args))


class InitCommand(Command):
    """Init command executor"""
    def get_child_address(self) -> Address:
        host, port = ip_address(self.args[0]), int(self.args[1])
        return Address(host, port)

    def execute(self) -> str:
        child = self.get_child_address()
        LOG.info("Child address: {}".format(child))
        if child in self.storage.get_childs():
            LOG.info("Already have child: {}".format(child))
            return "ALREADY"

        LOG.info("Adding child: {}".format(child))
        self.storage.add_child(child)
        return "OK"
    
    def __str__(self) -> str:
        child = self.get_child_address()
        return "{} INIT {} {}".format(self.hash, child.host, child.port)

class ChildCommand(Command):
    """ Randomly selects a child host in the storage to redirect. 
        Then adds a child to self storage
    """

    def get_child_address(self) -> Address:
        host, port = ip_address(self.args[0]), int(self.args[1])
        return Address(host, port)

    def execute(self) -> str:
        child_to_add = self.get_child_address()
        client = SocketClient(self.options)
        childs = self.storage.get_childs()

        LOG.info("Randomly selected child for forwarding")
        if childs:  
            child = random.choice(childs)
            LOG.info("Child {} was selected".format(child))
            client.change_destination(child)
            report = client.send_message(str(self))
            LOG.info("Child {} response report `{}`".format(report))
        else:
            LOG.info("Not found child in storage. Forwarding canceled")

        self.storage.add_child(child_to_add)
        return "OK"

    def __str__(self) -> str:
        child_to_add = self.get_child_address()
        return "{} ADD_CHILD {}".format(self.hash, child_to_add)


class CommandParser:
    @staticmethod
    def support_commands() -> List[Command]:
        commands = [
            (name, cls)
            for name, cls in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(cls) and issubclass(cls, Command) and type(cls) != Command
        ]
        return commands

    @staticmethod
    def get_command(
        decoded_data: str, storage: BaseStorage, 
        options: NetworkOptions, delimiter: str = " ") -> Optional[Command]:
        support_commands = CommandParser.support_commands()
        LOG.info("Support commands is {}".format([
            cmd_name for cmd_name, _ in support_commands])
        )

        decoded_hash, decoded_name, *decoded_args = decoded_data.split(delimiter)
        LOG.info("Parsed values: hash={}, name={}, args={}".format(
            decoded_hash, decoded_name, decoded_args))

        for command_name, command_cls in support_commands:
            if command_name.lower().startswith(decoded_name.lower()):
                return command_cls(decoded_hash, storage, options, decoded_args)
