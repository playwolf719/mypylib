#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/7/31 9:37
# @Author  : cbdeng
# @Software: PyCharm
import json
from enum import Enum
import functools
from lru import LRU
import inspect
import hashlib
import os
import configparser
import copy
import logging
from logging.handlers import RotatingFileHandler
import sys

# handler = RotatingFileHandler('/var/log/uwsgi/qademo_app.log', maxBytes=10**8, backupCount=1)
# mylogger = logging.getLogger('qademo')
# mylogger.setLevel(logging.INFO)
# mylogger.addHandler(handler)


current_dir, filename = os.path.split(os.path.realpath(__file__))
formatter = logging.Formatter('%(asctime)s  %(levelname)s %(message)s')

# add formatter to ch
# def get_logger(log_file_path="/var/log/uwsgi/qademo_myapp.log"):
#     if "qademo_myapp" in log_file_path:
#         logging.basicConfig(filename = log_file_path,filemode='a',level=logging.WARNING, format = '%(asctime)s  %(filename)s : %(levelname)s  %(message)s',)
#     else:
#         logging.basicConfig(filename = log_file_path,filemode='a',level=logging.WARNING, format = '%(asctime)s  %(filename)s : %(levelname)s  %(message)s',)
#     return logging
def setup_logger(name, log_file=current_dir+"/../../log/app.log",is_stdout=False, level=logging.INFO):
    """Function setup as many loggers as you want"""
    if is_stdout:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
g_stdlogging = setup_logger("std",is_stdout=True)
g_mylogging = g_stdlogging

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)

LRU_DICT = {}

# 建议用于key少，耗时少的场景
def lru_cache(max_len=10000, exclude_list=[]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            max_lru_dict_len = 1000
            # print("@"*20)
            # 包路径名+类名(非类的话，该值为<class 'str'>)+方法名
            lru_dict_key = str(inspect.getmodule(func)) + ":" + str(args[0].__class__) + ":" + func.__name__
            tmp_dict = {}
            if exclude_list:
                for key, val in kwargs.items():
                    if key not in exclude_list:
                        tmp_dict[key] = val
            kwargs = tmp_dict
            tmp_args = [str(v) for v in list(args)]
            # 普通方法
            if tmp_args[0].__class__.__module__ == "builtins":
                input_key = "^^".join(tmp_args) + ":" + str(kwargs)
            # 实例或类方法
            else:
                input_key = "^^".join(tmp_args[1:]) + ":" + str(kwargs)
            if len(LRU_DICT) > max_lru_dict_len:
                g_stdlogging.warning("[lru_cache]LRU_DICT length bigger than 10000")
            if len(lru_dict_key) > 255:
                lru_dict_key = hashlib.md5(lru_dict_key.encode("utf-8")).hexdigest()
            if len(input_key) > 255:
                input_key = hashlib.md5(input_key.encode("utf-8")).hexdigest()
            if lru_dict_key in LRU_DICT:
                tmp_lru = LRU_DICT[lru_dict_key]
                if input_key in tmp_lru:
                    res = tmp_lru[input_key]
                    # print("input_key in tmp_lru,%s" % (res,))
                else:
                    res = func(*args, **kwargs)
                    tmp_lru[input_key] = res
                    LRU_DICT[lru_dict_key] = tmp_lru
                    # print("input_key not in tmp_lru,%s" % (res,))
            else:
                tmp_lru = LRU(max_len)
                res = func(*args, **kwargs)
                tmp_lru[input_key] = res
                LRU_DICT[lru_dict_key] = tmp_lru
                # print("lru_dict_key not in LRU_DICT %s" % (res,))
            return res

        return wrapper

    return decorator



def get_config(rel_path=""):
    """
    加载配置文件
    :param rel_path: 父目录
    :return:
    """
    # base_path = rel_path+"base.ini"
    local_path = rel_path+"local.ini"
    prod_path = rel_path+"prod.ini"
    # if not os.path.isfile(base_path):
    #     raise Exception("%s not found" % (base_path))
    if not os.path.isfile(local_path) and not os.path.isfile(prod_path):
        raise Exception("%s and %s not found" % (local_path, prod_path))
    config = configparser.ConfigParser()
    # config.read(base_path)
    if os.path.isfile(prod_path):
        config.read(prod_path)
    if os.path.isfile(local_path):
        config.read(local_path)
    config = copy.deepcopy(config._sections)
    return config

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z

g_local_conf = get_config(current_dir+"/../../conf/")


def get_host_list(sub_config):
    host_list = []
    multi_host_str = sub_config["multi_host"]
    tmp_host_list = multi_host_str.split(",")
    for item in tmp_host_list:
        tmp = item.split(":")
        if item and len(tmp) == 2 and tmp[0] and tmp[1]:
            host_list.append(item)
    if not host_list:
        raise Exception("[get_host_list] multi_host format err %s" % multi_host_str )
    return host_list