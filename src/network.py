from typing import Union
from pathlib import Path
import json
from ipaddress import ip_address, IPv4Address, IPv6Address


class Address:
    """Incapsulates bot location"""
    def __init__(self, host: Union[IPv4Address, IPv6Address], port: int) -> None:
        self._host, self.port = host, port

    @property
    def host(self) -> str:
        return str(self._host)

    @host.setter
    def host(self, value):
        self._host = ip_address(value)
    
    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, obj: object) -> bool:  
        if not obj: 
            return False          
        return self.host == obj.host and self.port == obj.port

    def __str__(self) -> str:
        return "{}:{}".format(self._host, self.port)

    def __repr__(self) -> str:
        return str(self)


class NetworkOptions:
    def __init__(
        self, path: Union[Path, None], address: Union[Address, None], 
        buffer_size: int, encoding: str) -> None:
    
        self.path, self.address = path, address
        self.buffer_size, self.encoding = buffer_size, encoding

        if not path: return

        if not self.path.exists():
            self.path.parent.mkdir(parents=True)
            self.path.touch()

            options = {
                "host": str(self.address.host),
                "port": self.address.port,
                "buffer_size": self.buffer_size,
                "encoding": self.encoding
            }
            
            with open(self.path, "w") as option_file:
                json.dump(options, option_file)
            
        else:
            with open(self.path, "r") as option_file:
                options = json.load(option_file)
                self.address.port = options["port"]

    def change_port(self, new_port: int) -> None:
        if new_port <= 0 or new_port >= 65536:
            raise ValueError("Invalid port {}".format(new_port))

        with open(self.path, "r") as option_file:
            options = json.load(option_file)
            options["port"] = new_port

        with open(self.path, "w") as option_file:
            json.dump(options, option_file)

        self.address.port = options["port"]
