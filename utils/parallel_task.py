#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/18 17:12
# @Author  : cbdeng
# @Software: PyCharm
from gevent import monkey; monkey.patch_socket()
import gevent
import time
import requests

def f(a,b=3):
    # gevent.sleep(  0.1)
    now = time.time()
    requests.get('http://121.42.36.80/')
    print("ff",time.time()-now)
    return b

class ParallelTask():
    def __init__(self):
        self.task_list = []


    def add_task(self,*args,**kwargs):
        self.task_list.append(gevent.spawn(args[0],*args[1:],**kwargs) )

    def doit(self):
        all_res = gevent.joinall(self.task_list)
        final_list = []
        for item in self.task_list:
            final_list.append(item.value)
        return final_list

if __name__=="__main__":
    ins = ParallelTask()
    now = time.time()
    ins.add_task(f,1,12)
    ins.add_task(f,2,b=11)
    ins.add_task(f,3,b=4)
    ins.doit()
    # print(ins.doit())
    print(time.time()-now)



