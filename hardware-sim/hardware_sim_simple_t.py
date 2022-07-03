from hardware_sim_simple import *  # 要实现的模块


class Xor(Module):  # 每个模块都要继承自 Module
    inputs = ('a', 1), ('b', 1)
    outputs = ('out', 1),

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
        Nand(a=a, b=b, out=wire0)  # Nand 是基础门，无需搭建
        Nand(a=a, b=wire0, out=wire1)
        Nand(a=b, b=wire0, out=wire2)
        Nand(a=wire1, b=wire2, out=out)


class Xor16(Module):
    inputs = ('a', 16), ('b', 16)
    outputs = ('out', 16),

    def build(self):
        a = self.a
        b = self.b
        out = self.out

        for i in range(16):
            Xor(a=a[i], b=b[i], out=out[i])


class Not(Module):
    inputs = ('in_', 1),
    outputs = ('out', 1),

    def build(self):
        in_, out = self.in_, self.out
        Nand(a=in_, b=in_, out=out)


class And(Module):
    inputs = ('a', 1), ('b', 1)
    outputs = ('out', 1),

    def build(self):
        a, b, out = self.a, self.b, self.out
        wire = Wire()
        Nand(a=a, b=b, out=wire)
        Not(in_=wire, out=out)


class Or(Module):
    inputs = ('a', 1), ('b', 1)
    outputs = ('out', 1),

    def build(self):
        a, b, out = self.a, self.b, self.out
        wire0, wire1 = Wire(), Wire()
        Not(in_=a, out=wire0)
        Not(in_=b, out=wire1)
        Nand(a=wire0, b=wire1, out=out)


class HalfAdder(Module):
    inputs = ('a', 1), ('b', 1)
    outputs = ('s', 1), ('c', 1)

    def build(self):
        a, b, s, c = self.a, self.b, self.s, self.c
        Xor(a=a, b=b, out=s)
        And(a=a, b=b, out=c)


class FullAdder(Module):
    inputs = ('a', 1), ('b', 1), ('ci', 1)
    outputs = ('s', 1), ('co', 1)

    def build(self):
        a, b, ci, s, co = self.a, self.b, self.ci, self.s, self.co
        wire0, wire1, wire2 = Wire(), Wire(), Wire()
        HalfAdder(a=a, b=b, s=wire0, c=wire1)
        HalfAdder(a=wire0, b=ci, s=s, c=wire2)
        Or(a=wire1, b=wire2, out=co)


class Adder16(Module):
    inputs = ('A', 16), ('B', 16), ('ci', 1)
    outputs = ('S', 16), ('co', 1)

    def build(self):
        A, B, ci, S, co = self.A, self.B, self.ci, self.S, self.co
        wires = [Wire() for _ in range(16)]
        for i in range(16):
            a_in, b_in, s_out = A[i], B[i], S[i]
            ci_in = ci if i == 0 else wires[i - 1]
            co_out = co if i == 15 else wires[i]
            FullAdder(a=a_in, b=b_in, ci=ci_in, s=s_out, co=co_out)


def xor_tb():
    def next_and_show():
        next_step(test)  # 使数据传递一步
        print(out.read())  # out.read() 读取导线 out 上的信息

    a = Wire()
    b = Wire()
    out = Wire()
    test = Xor(a=a, b=b, out=out)  # 要测试的模块
    values = '01'
    for a_ in values:
        for b_ in values:
            a.write(a_)  # 把 a_ 写入导线 a
            b.write(b_)
            next_and_show()  # 因为这个 Xor 有三级门延迟，所以需要三个
            next_and_show()
            next_and_show()
            print(f'end: a={a_}, b={b_}, out={out.read()}')


def xor16_tb():
    def next_and_show():
        next_step(test)
        print(out.read())

    def to_binary(value: int):
        res = ''
        while value:
            res = str(value & 1) + res
            value >>= 1
        return res

    a = Wire('a', 16)
    b = Wire('b', 16)
    out = Wire('out', 16)
    test = Xor16(a=a, b=b, out=out)
    test_values = (0b100, 0b1000), (0x1234, 0x1111), (0x1101, 0xffff)
    for a_, b_ in test_values:
        a_ = to_binary(a_)
        b_ = to_binary(b_)
        a.write(a_)
        b.write(b_)
        next_and_show()
        next_and_show()
        next_and_show()
        print(f"end: a=16'b{a.read()}, b=16'b{b.read()}, out=16'b{out.read()}")


def not_tb():
    in_ = Wire('in_')
    out = Wire('out')
    test = Not(in_=in_, out=out)
    for i in '01':
        in_.write(i)
        next_step(test)
        print(f'end: {in_.read()=}, {out.read()=}')


def two_inputs_tb(m: type[Module], time_steps: int):
    def next_n(n: int):
        for i in range(n):
            next_step(test)
    a = Wire('a')
    b = Wire('b')
    out = Wire('out')
    test = m(a=a, b=b, out=out)
    for a_ in '01':
        for b_ in '01':
            a.write(a_)
            b.write(b_)
            next_n(time_steps)
            print(f'{a.read()=}, {b.read()=}, {out.read()=}')


and_tb = lambda: two_inputs_tb(And, 2)
or_tb = lambda: two_inputs_tb(Or, 2)
nand_tb = lambda: two_inputs_tb(Nand, 2)


def half_adder_tb():
    def next_n(n: int):
        for i in range(n):
            next_step(test)

    a, b, s, c = Wire('a'), Wire('b'), Wire('s'), Wire('c')
    test = HalfAdder(a=a, b=b, s=s, c=c)
    for a_ in '01':
        for b_ in '01':
            a.write(a_)
            b.write(b_)
            next_n(3)
            print(f'{a.read()=}, {b.read()=}, {s.read()=}, {c.read()=}')


def full_adder_tb():
    def next_n(n: int):
        for i in range(n):
            next_step(test)

    a = Wire('a')
    b = Wire('b')
    ci = Wire('ci')
    s = Wire('s')
    co = Wire('co')
    test = FullAdder(a=a, b=b, ci=ci, s=s, co=co)
    values = '01'
    print('| a | b | ci | s | co |')
    print('|---|---|----|---|----|')
    for a_ in values:
        for b_ in values:
            for c_ in values:
                a.write(a_)
                b.write(b_)
                ci.write(c_)
                next_n(6)
                print(f'| {a.read()} | {b.read()} | {ci.read()}  | {s.read()} | {co.read()}  |')


def adder16_tb():
    def next_n(n):
        for i in range(n):
            next_step(test)

    def to_binary(value: int):
        res = ''
        while value:
            res = str(value & 1) + res
            value >>= 1
        return res

    A, B, ci, S, co = Wire('A', 16), Wire('B', 16), Wire('ci'), Wire('S', 16), Wire('co')
    test = Adder16(A=A, B=B, ci=ci, S=S, co=co)
    test_values = (0x1111, 0x2222, 0), (0x4444, 0x2323, 1), (0xFFFF, 0x0000, 1)
    print('A, B, ci, S, co = \\')
    for a, b, ci_ in test_values:
        a = to_binary(a)
        b = to_binary(b)
        A.write(a)
        B.write(b)
        ci.write(ci_)
        next_n(100)
        print(f'{A.read()}, {B.read()}, {ci.read()}, {S.read()}, {co.read()}')


if __name__ == '__main__':
    adder16_tb()
