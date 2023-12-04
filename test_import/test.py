from .test2 import *

hello = "Hello you"


def say_hello():
    return hello + " how today???"


def baba():
    return "babaaaa"


class TestClass():
    def __init__(self, a):
        self.a = a
        self.b = 5
        self.c = baba

    def build_str(self):
        res = ""
        for key, value in self.__dict__.items():
            res += f"{key} : {value}\n"

        return res

    def __str__(self):
        return self.build_str()
    

