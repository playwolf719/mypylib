#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/20 15:41
# @Author  : cbdeng
# @Software: PyCharm

from peewee import *
from common_lib.utils.conf_util import g_conf
from playhouse.pool import PooledMySQLDatabase
import functools
from common_lib.common_func import g_stdlogging
from common_lib.utils.common_exception import CommonException

database = None

def get_db():
    global database
    if not database:
        database = get_new_db()
    return database

def get_new_db():
    global database
    m_dict = g_conf["mysql"]
    # database = MySQLDatabase(m_dict["dbname"], **{'host': m_dict["host"], "passwd":m_dict["password"], 'port': int(m_dict["port"]), 'user': m_dict["uname"]})
    database = PooledMySQLDatabase(database='dociee', host=m_dict["host"], port=int(m_dict["port"]),user=m_dict["uname"], passwd=m_dict["password"],stale_timeout=300 )
    return database

class BaseModel(Model):
    class Meta:
        database = get_db()



def mu_catch():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = None
            if hasattr(args[0], 'Ins'):
                ins = args[0].Ins
            else:
                ins = args[0]
            try:
                res = func(*args, **kwargs)
            except CommonException as e:
                ins._meta.database.close()
                raise e
            except Exception as e:
                ins._meta.database.close()
                ins._meta.database = get_new_db()
                g_stdlogging.exception("[model_cls_catch] %s %s" % (func.__name__,e))
            ins._meta.database.close()
            return res
        return wrapper
    return decorator