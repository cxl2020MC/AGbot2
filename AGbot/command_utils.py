import shlex

class Command:
    def __init__(self, command_string: str) -> None:
        self.command_string = command_string
        self.command_list = shlex.split(command_string)

    def get_command_list(self) -> list:
        return self.command_list

    def get_command_name(self) -> str:
        return self.command_list[0][1:]
    
    def _get_command_args(self) -> list:
        return self.command_list[1:]
    
    def get_kwarg(self, long_arg: str, short_arg: str|None = None, default: str|None = None) -> str|None:
        for i in self._get_command_args():
            if i.startswith(f"--{long_arg}="):
                return i.split('=')[1]
            elif short_arg is not None and i.startswith(f"-{short_arg}="):
                return i.split('=')[1]
        return default

    def get_kwarg_bool(self, long_arg: str, short_arg: str|None = None, default: bool = False) -> bool:
        command_args = self._get_command_args()
        if f"--{long_arg}" in command_args:
            return True
        elif f"-{short_arg}" in command_args:
            return True
        return default
    
    def get_arg(self, index: int, default: str|None = None) -> str|None:
        try:
            return self._get_command_args()[index]
        except IndexError:
            return default


class CommandInputError(Exception):
    pass


if __name__ == "__main__":
    command = Command("/agbot -a=1 -b=2 -c=3")
    print(command.get_command_list())
    print(command.get_command_name())
    print(command.get_kwarg("a", "a"))