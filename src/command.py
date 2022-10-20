import subprocess
from typing import Tuple, Dict
from abc import ABC, abstractmethod


class Command(ABC):
    """Command interface"""
    def __init__(
        self, name: str = "", args: Tuple[str] = tuple(), **kwargs: Dict[str, str]) -> None:

        self.name, self.args = name, args
        for arg_name, arg_value in kwargs.items():
            setattr(self, arg_name, arg_value)

    @abstractmethod
    def execute(self) -> str:
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


class ChildCommand(Command):
    """ Randomly selects a child host in the storage to redirect.
        Then adds a child to self storage"""
    def execute(self) -> str:
        # <self.storage: BaseStorage>, <self.child: Address>, <self.options_template>
        # TODO, using client to redirect the request
        pass
