from hardware_sim_simpleS import *  # 为了表示不同，在模块名结尾加上 S

size = 4


class Xor(Module):
    a: Input  # 表示 a 是一个输入，位宽是 1
    b: Input
    out: Output  # 表示 out 是一个输出，位宽是 1

    def build(self):
        # 输入
        a = self.a
        b = self.b
        # 输出
        out = self.out
        # 内部导线
        wire0 = Wire()
        wire1 = Wire()
        wire2 = Wire()
        # 构造
        Nand(a=a, b=b, out=wire0)
        Nand(a=a, b=wire0, out=wire1)
        Nand(a=b, b=wire0, out=wire2)
        Nand(a=wire1, b=wire2, out=out)


class XorTest(Testbench[Xor]):  # 测试类的基类是 Testbench，带 [] 可以自动生成测试
    pass


class XorSize(Module):
    a: Input[size]
    b: Input[size]
    out: Output[size]

    def build(self):
        a = self.a
        b = self.b
        out = self.out

        for i in range(size):
            Xor(a=a[i], b=b[i], out=out[i])


class XorSizeTest(Testbench[XorSize]):
    pass


def main():
    from hardware_sim_simpleS import _gen_bin
    # 初始化
    inputs = ('a', size), ('b', size)
    outputs = ('out', size),
    kwargs: dict[str, Wire] = {}
    for name, width in inputs + outputs:
        kwargs[name] = Wire(name, width)
    # 生成数据
    pos = 0
    name2pos = {}
    for name, width in inputs:
        name2pos[name] = pos, pos + width
        pos += width
    res: dict[str, list[str]] = {}
    for data in _gen_bin(pos):
        for name, pos in name2pos.items():
            kwargs[name].write(data[pos[0]:pos[1]])
        kwargs['out'].write(format(int(kwargs['a'].read().replace('x', '0').replace('z', '0'), 2)
                                   ^ int(kwargs['b'].read().replace('x', '0').replace('z', '0'), 2), '0b'))
        output = []
        for name, _ in outputs:
            output.append(kwargs[name].read())
        res[data] = output
    # 输出数据
    names = [name for name, _ in inputs + outputs]
    lines: list[list[str]] = []
    for data, output in res.items():
        line = []
        for name, pos in name2pos.items():
            line.append(data[pos[0]:pos[1]])
        for o in output:
            line.append(o.replace('x', '0').replace('z', '0'))
        lines.append([str(i) for i in line])
    most_width = 0  # 对齐
    for lst in [names, *lines]:
        for value in lst:
            length = len(value)
            if length > most_width:
                most_width = length
    str_res = []
    for line in [names] + lines:
        str_res.append('| ' + ' | '.join(f'{i:{most_width}}' for i in line) + ' |')
        if line is names:  # 输出分隔线
            str_res.append(('|' + '-' * (most_width + 2)) * 3 + '|')
    print('\n'.join(str_res))


if __name__ == '__main__':
    XorSizeTest.run()
    # main()
