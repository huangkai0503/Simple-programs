from typing import ClassVar

port_t = ClassVar[tuple[tuple[str, int], ...]]

now_module: 'Module | None' = None
all_wires: list['Wire'] = []


class Module:
    __slots__ = 'ports', 'sub_modules'

    inputs: port_t
    outputs: port_t

    ports: dict[str, 'Wire']
    sub_modules: list['Module']

    def __init__(self, **kwargs: 'Wire'):
        global now_module
        raw_now = now_module
        if now_module is not None:
            now_module.sub_modules.append(self)
        now_module = self

        self.sub_modules = []
        ports = self.ports = {}

        inputs = self.inputs
        outputs = self.outputs
        input_names = {tup[0] for tup in inputs}
        name2width = {tup[0]: tup[1] for tup in (inputs + outputs)}
        names = name2width.keys()
        for key, value in kwargs.items():
            if key in names:
                real, expect = value.width(), name2width[key]
                if real != expect:
                    raise ValueError(f"{key} 对应的值的位宽（{real}）和期待的位宽（{expect}）不匹配")
                ports[key] = value
            else:
                raise ValueError(f"{type(self).__name__} 没有名为 {key} 的端口")
        for name in input_names - set(kwargs.keys()):
            new = Wire(f'<default {name} port>')
            new.write('z')
            ports[name] = new
        self.build()
        now_module = raw_now

    def flush(self):
        for m in self.sub_modules:
            m.flush()
        # 刷新输出，使输出可以立即变化
        ports = self.ports
        for tup in self.outputs:
            output = tup[0]
            if output in ports.keys():
                ports[output].flush()

    def build(self):
        raise NotImplementedError

    def __getattr__(self, item: str):
        ports = self.ports
        if item in ports.keys():
            return ports[item]
        raise ValueError(f"模块 {type(self).__name__} 中没有名为 {item} 的端口")


class Wire:
    name: str | None  # 该导线的名字（可以为 None）
    _value: str  # 该导线上的值（四值逻辑），字符串长度就是导线长度，初始是不定态 x
    _new_value: str  # 新值，调用 flush() 时会刷新

    def __init__(self, name: str = None, width: int = 1):
        self.name = name
        self._value = 'x' * width
        self._new_value = 'x' * width
        all_wires.append(self)

    def read(self) -> str:
        return self._value

    def write(self, data: int | str):
        data = str(data)
        length = len(data)
        width = len(self._value)
        if length < width:
            data = '0' * (width - length) + data
        self._new_value = data

    def flush(self):
        self._value = self._new_value

    def width(self):
        return len(self._value)

    def __getitem__(self, item: int | slice) -> 'Wire':
        if isinstance(item, int):
            pos = slice(item, item + 1)
        elif item.step is not None:
            raise ValueError(f"{item} 的步长只能为 1")
        else:
            start, stop = item.start, item.stop
            if start is None:
                start = 0
            if stop is None:
                stop = len(self._value) + 1
            pos = slice(start, stop)
        return _SubWire(self, pos)


class _SubWire(Wire):
    parent: Wire  # 父导线
    pos: slice  # 在父导线中的位置

    def __init__(self, parent: Wire, pos: slice):
        start, stop = pos.start, pos.stop
        super().__init__(f'{parent.name}[{start}: {stop}]', stop - start)
        width = len(parent._value)
        self.pos = slice(width - stop, width - start)  # 因为低位在右，所以要倒着数
        self.parent = parent

    def write(self, data: int | str):
        super().write(data)
        parent = self.parent
        parent_value = list(parent._new_value)
        parent_value[self.pos] = list(data)
        parent.write(''.join(parent_value))

    def read(self) -> str:
        return self.parent._value[self.pos]


class Nand(Module):
    inputs = ('a', 1), ('b', 1)
    outputs = ('out', 1),

    def build(self):
        pass

    def flush(self):
        a, b = self.a.read(), self.b.read()
        write = self.out.write
        match a, b:
            case ('0', _) | (_, '0'):
                write('1')
            case ('1', 'x') | ('x', '1'):
                write('x')
            case ('x', 'x') | ('x', 'z') | ('z', 'x'):
                write('x')  # TODO: 是否要像 logisim 那样输出 E？
            case ('z', 'z'):
                write('z')
            case ('1', '1') | ('1', 'z') | ('z', '1'):
                write('0')
            case _:
                raise ValueError(f"未知 a, b 值：{a, b}")


def next_step(m: Module):
    for wire in all_wires:
        wire.flush()
    m.flush()
