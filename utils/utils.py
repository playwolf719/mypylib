#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/12 17:07
# @Author  : cbdeng
# @Software: PyCharm
import time
import functools
from common_lib.utils.conf_util import g_conf
import inspect
import logging
import json
from common_lib.db.redis import RedisClient
import jwt
from common_lib.utils.common_exception import req_format_err,no_login_err,auth_err
from flask import request
import datetime

from dateutil.parser import parse

g_test_user_list = ["1412@qq.com","1411@qq.com",
"57297229@qq.com",
"jiebour@hotmail.com",
"Cathygaogao@126.com",
"sunhuijie1993@qq.com",
"aiden.ddz@gmail.com",
"1194834105@qq.com",
"playwolf719@163.com",
"healootry0943@yahoo.com",]

# 记录耗时
def log_cost(env={}):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.time()
            res = func(*args, **kwargs)
            if "log_cost" in g_conf["PROJ_INFO"] and g_conf["PROJ_INFO"]["log_cost"] == "on":
                # curframe = inspect.currentframe()
                # calframe = inspect.getouterframes(curframe, 2)
                # mylogger.info("！！！！！[log_cost] caller name: %s && %s" % (calframe[1], func.__name__) )
                func_key = str(inspect.getmodule(func)) + ":" + str(args[0].__class__) + ":" + func.__name__
                args = [str(v) for v in list(args)]
                # 普通方法
                if args[0].__class__.__module__ == "builtins":
                    input_key = "^^".join(args) + ":" + str(kwargs)
                # 实例或类方法
                else:
                    input_key = "^^".join(args[1:]) + ":" + str(kwargs)
                final_key = func_key+"@@"+input_key+"@@"+str(inspect.stack()[1][3])
                the_time = time.time()
                diff = the_time - t0
                if diff >= 0.1:
                    logging.warning("[log_cost]  the_time : %s ;final_key : %s ; diff : %.6f;" % (the_time,final_key,diff))
                    # logging.info("[log_cost]  final_key : %s ; diff : %.6f;" % (final_key,diff))
            return res
        return wrapper
    return decorator

def ret_in_json(data={},code=1,msg="操作成功"):
    if type(data) is not dict:
        raise Exception("[ret_in_json]data must be dict")
    the_res = {
        "code":code,
        "msg":msg,
        "data": data
    }
    # return json.dumps(the_res, indent=4, ensure_ascii=False,separators=(',', ':'))
    return json.dumps(the_res,ensure_ascii=False)

def str_is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def freq_control_by_key(key,duration=600,max_times=10):
    cli = RedisClient().get_cli()
    now_times = cli.get(key)
    if not now_times:
        cli.incr(key)
        cli.expire(key,duration)
    else:
        now_times = int(now_times)
        if now_times >= max_times:
            return False
        else:
            cli.incr(key)
    return True

def freq_control_coupon_by_key(key,coupon,duration=600,max_size=10):
    cli = RedisClient().get_cli()
    coupon_size = 0
    try:
        coupon_size = cli.scard(key)
    except Exception as e:
        logging.error("[freq_control_coupon_by_key]%s" % e)
    if not coupon_size:
        cli.sadd(key,coupon)
        cli.expire(key,duration)
    elif coupon_size>=max_size:
        return False
    else:
        cli.sadd(key,coupon)
    return True

def get_user_info_by_jwt(token):
    try:
        res = jwt.decode(token, 'x4DxG89LY0C9GMwx08IA', algorithms=['HS256'])
        return res
    except jwt.exceptions.ExpiredSignatureError as e:
        return None
    except Exception as e:
        logging.error("[get_user_info_by_jwt]%s" % e)
        return None


def get_user_info_by_auth():
    auth_res = request.headers.get('Authorization', None)
    if not auth_res:
        return None
    auth_res = auth_res.split(" ")
    auth_res = [x for x in auth_res if x]
    if len(auth_res)!=2 and not auth_res[1]:
        # raise Exception("[get_user_info_by_jwt]auth err %s " % (auth,))
        raise req_format_err
    auth_res = get_user_info_by_jwt(auth_res[1])
    return auth_res

def get_dtstr_by_ts(ts=None):
    if not ts:
        ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def get_ts8dtstr(dtstr):
    return int(time.mktime(datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S").timetuple()))


def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False