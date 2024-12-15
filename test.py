import shlex

class CommandLineParser:
    def __init__(self):
        self.positional_args = []
        self.options = {}

    def add_argument(self, *args, **kwargs):
        for arg in args:
            self.options.setdefault(arg, kwargs.get('default', None))

    def parse_args(self, command_str):
        tokens = shlex.split(command_str)

        for i, token in enumerate(tokens):
            if token.startswith('-'):
                if token in self.options:
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                        self.options[token] = tokens[i + 1]
                        i += 1
                    elif self.options[token] is None:
                        self.options[token] = True
                    else:
                        raise ValueError(f"Option {token} requires an argument")
                else:
                    raise ValueError(f"Unknown option: {token}")
            else:
                self.positional_args.append(token)

        return self

    def __str__(self):
        return f"Positional arguments: {self.positional_args}\nOptions: {self.options}"

# 创建解析器实例
parser = CommandLineParser()

# 添加命令行参数
parser.add_argument('command', help='The main command')
parser.add_argument('-f', '--file', help='File to process', default=None)
parser.add_argument('-v', '--verbose', help='Enable verbose mode', action='store_true')

# 解析命令行字符串
command_str = 'main_command -f file.txt -v'
parsed_args = parser.parse_args(command_str)

# 打印解析结果
print(parsed_args)