from typing import Generic, TypeVar

from hardware_sim_simple import Module as _Module, Wire, Nand, all_wires

size = TypeVar('size')


class Module(_Module):
    def build(self):
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        inputs = []
        outputs = []

        for attr, t in cls.__annotations__.items():
            if t is Input:
                inputs.append((attr, 1))
            elif t is Output:
                outputs.append((attr, 1))
            t = str(t)
            if 'Input[' in t:  # 因为开头可能带有模块名，所以不能使用 t.startswith('Input[')
                inputs.append((attr, int(t[t.find('Input[') + 6:-1])))  # 用于获取方括号中的内容
            elif 'Output[' in t:
                outputs.append((attr, int(t[t.find('Output[') + 7:-1])))

        cls.inputs = tuple(inputs)
        cls.outputs = tuple(outputs)


class Input(Wire, Generic[size]): pass
class Output(Wire, Generic[size]): pass


class Testbench:
    @classmethod
    def run(cls):
        pass

    def __class_getitem__(cls, item):
        class _Sub(cls):
            test_type = item

            @classmethod
            def run(cls):
                _run(cls.test_type)
        return _Sub


def run_until_stop(m: Module):
    _all_wires = all_wires.copy()
    time = 0
    first_loop = True
    while True:
        same = True
        for wire in _all_wires:  # 因为子导线的存在，这里需要复制，不然遍历时大小会改变
            raw_value = wire.read()  # 不建议直接访问私有变量 _value 和 _new_value
            wire.flush()
            new_value = wire.read()
            if raw_value != new_value:
                same = False
        m.flush()
        if same and not first_loop:
            break
        first_loop = False
        time += 1
    return time


def _gen_bin(width: int) -> tuple[str, ...]:
    if width == 1:
        return '0', '1'
    res = []
    for i in _gen_bin(width - 1):
        res.append(i + '0')
        res.append(i + '1')
    return tuple(res)


def _run(test_type: type[Module]):
    # 初始化
    inputs = test_type.inputs
    outputs = test_type.outputs
    kwargs: dict[str, Wire] = {}
    for name, width in inputs + outputs:
        kwargs[name] = Wire(name, width)
    test = test_type(**kwargs)
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
        run_until_stop(test)
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
            line.append(int(data[pos[0]:pos[1]], 2))
        for o in output:
            line.append(int(o, 2))
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
