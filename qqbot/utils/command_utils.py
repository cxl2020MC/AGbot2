class CommandParser:
    def __init__(self, cmd: str):
        self.cmd = cmd
        self.args = []
        self.flags = {}
        self.__last_flag = ""
        self.c1 = 0
        self.c2 = 0
        self.parse()

    def parse(self):
        tmp = self.cmd
        while tmp:
            self.c1 += 1
            # 处理换行、转义字符7
            if tmp[0] in "\t\r\n\\":
                tmp = tmp[1:]
                continue
            # 处理普通参数分隔符空格
            if tmp[0] == " " and self.__last_flag == "":
                tmp = tmp[1:]
                continue
            # 处理长选项 --xxx
            if tmp.startswith("--"):
                flag, tmp = self.__get_sep(tmp[2:])
                self.__last_flag = flag
                self.flags[flag] = True
                continue
            # 处理短选项 -x
            if tmp.startswith("-"):
                flag, tmp = self.__get_sep(tmp[1:])
                if len(flag) == 1:
                    self.__last_flag = flag
                for c in flag:
                    self.flags[c] = True
                continue
            # 处理flag后面的值（分隔符：空格 / = / ,）
            if self.__last_flag and tmp[0] in " =,":
                this_sep = tmp[0]
                opt, tmp = self.__get_sep(tmp[1:])
                # flag第一次赋值
                if (
                    isinstance(self.flags[self.__last_flag], bool)
                    and self.flags[self.__last_flag] is True
                ):
                    if this_sep == ",":
                        raise ValueError(
                            f"flag参数{self.__last_flag}的第一个参数不能使用,分隔符 at {len(self.cmd) - len(tmp)}"
                        )
                    self.flags[self.__last_flag] = opt
                    continue
                # 分隔符不是逗号 → flag取值结束，这个opt是普通位置参数
                if this_sep == " ":
                    self.__last_flag = ""
                    self.args.append(opt)
                    continue
                # 逗号：追加到flag，变成列表
                old_opt = self.flags[self.__last_flag]
                if isinstance(old_opt, list):
                    old_opt.append(opt)
                else:
                    self.flags[self.__last_flag] = [old_opt, opt]
                continue
            # 补充错误格式的处理办法，不是flag但是使用了=/,
            if not self.__last_flag and tmp[0] in "=,":
                raise ValueError(
                    f"非flag参数不能使用{tmp[0]}分隔符 at {len(self.cmd) - len(tmp)}"
                )
            # 普通位置参数
            opt, tmp = self.__get_sep(tmp)
            self.args.append(opt)

    def __get_sep(self, s1: str) -> tuple[str, str]:
        quote = ""
        l = len(s1)
        i = 0

        while i < len(s1):
            self.c2 += 1
            c = s1[i]

            if c in "\"'`" and ((not quote) or quote == c):  # 引号包裹
                if i - 1 >= 0 and s1[i - 1] == "\\":  # 转义
                    s1 = s1[: i - 1] + s1[i:] + " "
                    i -= 1
                    l -= 1
                    continue

                if quote:
                    return s1[1 : i - 1], s1[i + 1 : l]  # 字符串结束了

                quote = c
                i += 1
                continue

            if not quote and c == "\\":
                s1 = s1[:i] + s1[i + 1 :] + " "
                l -= 1
                # 删除当前反斜杠后，后面的字符会移到 i 位置，需要重新检查 i
                continue

            if not quote and c in "|\\ \n\r=,":
                return s1[:i], s1[i:l]

            i += 1

        if quote:
            raise ValueError(f"未关闭的引号包裹：{quote} at {len(self.cmd)}")

        return s1, ""


if __name__ == "__main__":
    # 测试样例：引号包裹，里面有逗号
    parser = CommandParser(r'ls -l --color="3e33ee,ss" ddededd\swwswwswsws')
    print("args:", parser.args)
    print("flags:", parser.flags)
    print("c1:", parser.c1)
    print("c2:", parser.c2)

    # 测试转义 \"
    parser2 = CommandParser(r'echo --msg="hello \"world\",test" aaa')
    print("\nargs:", parser2.args)
    print("flags:", parser2.flags)
    print("c1:", parser2.c1)
    print("c2:", parser2.c2)

    # 测试逗号多值
    parser3 = CommandParser(r"run -v ab,bn,c end")
    print("\nargs:", parser3.args)
    print("flags:", parser3.flags)
    print("c1:", parser3.c1)
    print("c2:", parser3.c2)

    # 测试多单字节flag
    parser3 = CommandParser(r"run -abcdefg")
    print("\nargs:", parser3.args)
    print("flags:", parser3.flags)
    print("c1:", parser3.c1)
    print("c2:", parser3.c2)
