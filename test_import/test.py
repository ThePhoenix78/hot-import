hello = "Hello"


def say_hello():
    return hello + " how today???"


def baba():
    return "babaaaa"


class TestClass():
    def __init__(self, a=1):
        self.a = a
        self.b = 5
        self.c = baba

    def test(self):
        return "yes"

    def build_str(self):
        res = ""
        for key, value in self.__dict__.items():
            res += f"{key} : {value}\n"

        return res

    def __str__(self):
        return self.build_str()
    

