#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/6 9:13
# @Author  : cbdeng
# @Software: PyCharm
import os
import copy
import configparser

def get_conf_from_file(rel_path=""):
    """
    加载配置文件
    :param rel_path: conf目录
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

current_dir, filename = os.path.split(os.path.realpath(__file__))
g_conf = get_conf_from_file(current_dir+"/../../../conf/")