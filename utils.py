# coding: utf-8

from time import perf_counter as _perf_counter

def perf_counter():
    '''
    获取一个性能计数器, 执行返回函数来结束计时, 并返回保留两位小数的毫秒值
    '''
    start = _perf_counter()
    return lambda: round((_perf_counter() - start)*1000, 2)
