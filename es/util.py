#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/6/4 15:08
# @Author  : cbdeng
# @Software: PyCharm

import requests
import json
import os,sys

from common_lib.utils.conf_util import g_conf
import re
from peewee import *
from common_lib.common_func import g_stdlogging

g_es_host = ""

if "es" in g_conf:
    g_es_host = "http://%s:%s" % (g_conf["es"]["host"],g_conf["es"]["port"])

def req_es(uri,data={},method="put"):
    method_to_call = getattr(requests, method)
    url = '%s%s' % (g_es_host,uri)
    # print(url,data,method)
    headers = {'content-type': 'application/json'}
    r = method_to_call('%s' % (url),data=json.dumps(data), headers=headers)
    return r


def add_index(index,index_info):
    res = req_es("/"+index,index_info,method="put")
    # print(res.json())

def add_one(index,doc_type,data,):
    res = req_es("/%s/%s" % (index,doc_type),data=data,method="post")
    # print(res.json())
    return res

def del_by_query(index,query):
    res = req_es("/%s/_delete_by_query" % (index,),data=query,method="post")
    return res

def del_index(index):
    res = req_es("/"+index,method="delete")
    # print(res)


def query(index,doc_type,data):
    res = req_es("/%s/%s/_search" % (index,doc_type),data=data,method="get")
    res = res.json()
    # res = escli.search(index=index,doc_type=doc_type, body={"query": {"match": {"data": "张"}}})
    # print(res)
    # print("--------")
    # for item in res['hits']['hits']:
    #     print(item)
    return res