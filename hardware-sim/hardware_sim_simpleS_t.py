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


class SRLatch(Module):
    s_: Input
    r_: Input
    q: Output
    q_: Output  # 结尾带 _ 表示反逻辑

    def build(self):
        s_, r_, q, q_ = self.s_, self.r_, self.q, self.q_
        Nand(a=s_, b=self.q_, out=self.q)
        Nand(a=r_, b=self.q, out=self.q_)


class SRLatchTest(Testbench):
    @classmethod
    def run(cls):
        s_ = Wire('s_')
        r_ = Wire('r_')
        q = Wire('q')
        q_ = Wire('q_')
        test = SRLatch(s_=s_, r_=r_, q=q, q_=q_)
        print('s_, r_, q, q_ = ...')
        for s_value, r_value in ('01', '11', '10', '11'):
            s_.write(s_value)
            r_.write(r_value)
            run_until_stop(test)
            print(s_.read(), r_.read(), q.read(), q_.read())


if __name__ == '__main__':
    SRLatchTest.run()
