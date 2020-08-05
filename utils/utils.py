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
import jwt,re,os
from common_lib.utils.common_exception import req_format_err,no_login_err,auth_err,unknown_err
from flask import request
import datetime

from dateutil.parser import parse
import socket
import pickle
import hashlib
from common_lib.common_func import g_stdlogging
import xml.etree.ElementTree as ET
from ymutil.const import g_auth_key_pre
from urllib.parse import urlencode


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

def ret_in_json(data={},code=1,msg="操作成功！"):
    if type(data) is not dict:
        raise Exception("[ret_in_json]data must be dict")
    the_res = {
        "code":code,
        "msg":msg,
        "data": data
    }
    return json.dumps(the_res,ensure_ascii=False)


def ret_in_dict(data={},code=1,msg="操作成功"):
    if type(data) is not dict:
        raise Exception("[ret_in_json]data must be dict")
    the_res = {
        "code":code,
        "msg":msg,
        "data": data
    }
    # return json.dumps(the_res, indent=4, ensure_ascii=False,separators=(',', ':'))
    return the_res


def ret_in_json_dp(data={},code=200,msg="操作成功"):
    # if type(data) is not dict:
    #     raise Exception("[ret_in_json]data must be dict")
    the_res = {
        "code":code,
        "msg":msg,
        "data": data
    }
    # return json.dumps(the_res, indent=4, ensure_ascii=False,separators=(',', ':'))
    return json.dumps(the_res,ensure_ascii=False)

def str_is_int(s):
    try:
        s = s.replace(",","")
        int(s)
        return True
    except ValueError:
        return False

def str_is_float(s):
    try:
        s = s.replace(",","")
        float(s)
        return True
    except ValueError:
        return False

# 非高并发可用
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

from qiniu import Auth,put_file, etag,urlsafe_base64_encode,PersistentFop

access_key = "Ff15wlg7ywP59Zn-h89w0J9hzOoJoFkCBDaCfRh9"
secret_key = "e4OfFBTc2ltwzPnQdL9HNj48XFhhL1OED_iCAzp1"
from flask import current_app as app
import urllib,random

g_bucket_name = "ym512"

def get_dt_url(klist,pic_host="",dur=50):
    if not klist:
        return
    part_str = ""
    for k in klist:
        part_str += "/key/"+urlsafe_base64_encode(str(k))
    if not pic_host:
        pic_host = app.config["PIC_HOST"]
    url = pic_host+"/"+klist[0]+'?animate/duration/%s/merge%s' % (dur,part_str)
    return url


def up2cloud_video(filename,abs_filepath,need_rm = True,pic_host=""):
    ckey = "up2cloud_video1"
    thekey = filename
    rcli = RedisClient().get_cli()
    thetoken = rcli.get(ckey)
    if thetoken:
        thetoken = json.loads(thetoken)
    else:
        q = Auth(access_key, secret_key)
        # 上传后保存的文件名
        # 生成上传 Token，可以指定过期时间等
        ttl = 3600
        pat = urlsafe_base64_encode("videodt-$(count)")
        policy = {
            # "persistentOps": "vsample/jpg/ss/1/t/4/s/480x360/interval/1/pattern/dmZyYW1lLSQoY291bnQp",
            "persistentOps": "vsample/jpg/ss/0/t/15/interval/1/pattern/%s" % pat,
            "persistentNotifyUrl": "https://balimiao.cn/front/qiniu/video_dt_callback"
        }
        thetoken = q.upload_token(g_bucket_name, None, ttl,policy)
        rcli.set(ckey,json.dumps(thetoken),ex=ttl-600)
    # 要上传文件的本地路径
    ret, info = put_file(thetoken, thekey, abs_filepath)
    uri = ""
    if ret and ret["key"] == thekey and ret['hash'] == etag(abs_filepath):
        uri = json.loads(info.text_body)["key"]
    if not uri:
        g_stdlogging.error("[up2cloud_video]%s %s" % (ret, info))
        raise unknown_err
    # print(abs_filepath)
    if need_rm:
        os.remove(abs_filepath)
    if not pic_host:
        pic_host = app.config["PIC_HOST"]
    return pic_host+"/"+ uri

def trig_video_part(key):
    q = Auth(access_key, secret_key)
    # 要转码的文件所在的空间和文件名。
    bucket = g_bucket_name
    # 转码是使用的队列名称。
    pipeline = 'video_handle'
    pat = urlsafe_base64_encode("videopart-$(count)")
    # 要进行转码的转码操作。
    fops = "segment/mp4/segtime/5/pattern/%s" % pat
    # 可以对转码后的文件进行使用saveas参数自定义命名，当然也可以不指定文件会默认命名并保存在当前空间
    # saveas_key = urlsafe_base64_encode(g_bucket_name+':自定义文件key')
    # fops = fops + '|saveas/' + saveas_key
    pfop = PersistentFop(q, bucket, pipeline,notify_url="https://balimiao.cn/front/qiniu/video_part_callback")
    ops = []
    ops.append(fops)
    ret, info = pfop.execute(key, ops, 1)
    if "persistentId" in ret and ret["persistentId"]:
        return True
    else:
        g_stdlogging.exception("[trig_video_part]%s %s" % (ret,info))

def up2cloud_video_part(filename,abs_filepath,need_rm = True,pic_host=""):
    ckey = "up2cloud_video_part1"
    thekey = filename
    rcli = RedisClient().get_cli()
    thetoken = rcli.get(ckey)
    if False and thetoken:
        thetoken = json.loads(thetoken)
    else:
        q = Auth(access_key, secret_key)
        # 上传后保存的文件名
        # 生成上传 Token，可以指定过期时间等
        ttl = 3600
        pat = urlsafe_base64_encode("videopart-$(count)")
        policy = {
            # "persistentOps": "vsample/jpg/ss/1/t/4/s/480x360/interval/1/pattern/dmZyYW1lLSQoY291bnQp",
            "persistentOps": "segment/mp4/segtime/5/pattern/%s" % pat,
            "persistentNotifyUrl": "https://balimiao.cn/front/qiniu/video_part_callback"
        }
        thetoken = q.upload_token(g_bucket_name, None, ttl,policy)
        rcli.set(ckey,json.dumps(thetoken),ex=ttl-600)
    # 要上传文件的本地路径
    ret, info = put_file(thetoken, thekey, abs_filepath)
    uri = ""
    if ret and ret["key"] == thekey and ret['hash'] == etag(abs_filepath):
        uri = json.loads(info.text_body)["key"]
    if not uri:
        g_stdlogging.error("[up2cloud_video]%s %s" % (ret, info))
        raise unknown_err
    # print(abs_filepath)
    if need_rm:
        os.remove(abs_filepath)
    if not pic_host:
        pic_host = app.config["PIC_HOST"]
    return pic_host+"/"+ uri

def up2cloud(filename,abs_filepath,need_rm = True,pic_host=""):
    ckey = "up2cloud"
    thekey = filename
    rcli = RedisClient().get_cli()
    thetoken = rcli.get(ckey)
    if thetoken:
        thetoken = json.loads(thetoken)
    else:
        q = Auth(access_key, secret_key)
        # 上传后保存的文件名
        # 生成上传 Token，可以指定过期时间等
        ttl = 3600
        thetoken = q.upload_token(g_bucket_name, None, ttl)
        rcli.set(ckey,json.dumps(thetoken),ex=ttl-600)
    # 要上传文件的本地路径
    ret, info = put_file(thetoken, thekey, abs_filepath)
    uri = ""
    if ret and ret["key"] == thekey and ret['hash'] == etag(abs_filepath):
        uri = json.loads(info.text_body)["key"]
    if not uri:
        g_stdlogging.error("[up2cloud]%s %s" % (ret, info))
        raise unknown_err
    # print(abs_filepath)
    if need_rm:
        os.remove(abs_filepath)
    if not pic_host:
        pic_host = app.config["PIC_HOST"]
    return pic_host+"/"+ uri


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip

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

def is_str_json(input):
    try:
        json.loads(input)
    except Exception as e:
        return False
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

def get_num_from_str(input):
    return [int(s) for s in input.split() if s.isdigit()]

def get_user_info_by_auth_redis():
    auth_key = get_auth_key()
    if not auth_key:
        return None
    cli = RedisClient().get_cli()
    # res = cli.get(auth_key)
    res = cli.get(g_auth_key_pre+auth_key)
    if not res:
        return None
    return pickle.loads(res)

def get_auth_key():
    auth_key = request.cookies.get('token', None)
    if not auth_key:
        auth_key = request.headers.get('Authorization', None)
        if not auth_key:
            return None
    return auth_key

def is_str_phone(tn):
    reg = "1[0-9]{10}"
    return re.findall(reg, tn)

def get_uniq_list(seq):
    seen = set()
    res_list = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            res_list.append(item)
    return res_list


def get_dtstr_by_ts(ts=None):
    if not ts:
        ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def get_ts8dtstr(dtstr):
    return int(time.mktime(datetime.datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S").timetuple()))



def get_ts8dt(dt):
    if type(dt) == datetime.datetime:
        return int(time.mktime(dt.timetuple()))
    return dt


def get_dtstr8dt(dt):
    res = get_ts8dt(dt)
    return get_dtstr_by_ts(res)

def get_part_str(phone,start=3,length=4):
    ret_phone = ""
    if phone:
        num_list = list(phone)
        ret_phone = ""
        for index, item in enumerate(num_list):
            if index >= start and index < start + length:
                ret_phone = ret_phone + "*"
            else:
                ret_phone = ret_phone + item
    return ret_phone

def get_param_by_url(url):
    return urllib.parse.parse_qsl(parse.urlsplit(url).query)

def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False

def get_md5(str):
    # 创建md5对象
    hl = hashlib.md5()
    hl.update(str.encode(encoding='utf-8'))
    return hl.hexdigest()


# 建议用于key较多的cahce场景
def rcache(exclude_list=[],timeout=600,ver="v30"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 包路径名+类名(非类的话，该值为参数的类型，如<class 'str'>或int)+方法名
            arg_part = ""
            if len(args) >= 1:
                arg_part = str(args[0].__class__)
            key_pre = str(inspect.getmodule(func)) + ":" + arg_part + ":" + func.__name__ +":"+str(ver)
            r_need_cache = kwargs.pop("r_need_cache", True)
            r_del_cache = kwargs.pop("r_del_cache",False)
            r_timeout = kwargs.pop("r_timeout",0)
            # kwargs中的默认值，获取不到，如要获取，必须传值
            tmp_dict = {}
            if exclude_list:
                for key, val in kwargs.items():
                    if key not in exclude_list:
                        tmp_dict[key] = val
                kwargs = tmp_dict
            sorted_values = sorted(kwargs.items(), key=lambda val: val[0])
            kwdata = urlencode(sorted_values)
            # 普通方法
            input_key = ""
            for item in args:
                tmp =  str(item.__class__)
                if "." in tmp:
                    input_key += tmp+"|"
                else:
                    input_key += str(item)+"|"
            input_key += kwdata

            # if not tmp_args or tmp_args[0].__class__.__module__ == "builtins":
            #     input_key = "^^".join(tmp_args) + ":" + kwdata
            # # 实例或类方法
            # else:
            #     input_key = "^^".join(tmp_args[1:]) + ":" + kwdata
            if len(input_key) > 255:
                input_key = hashlib.md5(input_key.encode("utf-8")).hexdigest()
            key = key_pre+"|"+input_key
            # print(key)
            cli = RedisClient().get_cli()
            if r_del_cache:
                cli.delete(key)
            if r_need_cache:
                res = cli.get(key)
                if not res:
                    res = func(*args, **kwargs)
                    if r_timeout:
                        cli.set(key,pickle.dumps(res),ex=r_timeout)
                    else:
                        cli.set(key,pickle.dumps(res),ex=timeout)
                else:
                    res = pickle.loads(res)
            else:
                res = func(*args, **kwargs)
            return res
        return wrapper
    return decorator

def get_url_GETParam(url):
    tmp = url.split("?")
    if len(tmp)!=2 or not tmp[1]:
        return {}
    tmp = tmp[1]
    tmp_list = tmp.split("&")
    res_dict = {}
    for item in tmp_list:
        tmp = item.split("=")
        if len(tmp)!=2:
            continue
        res_dict[tmp[0]] = tmp[1]
    return res_dict

def get_dict8xml(xmldata):
    res_dict = {}
    try:
        root = ET.fromstring(xmldata)
    except Exception as e:
        g_stdlogging.error("[get_dict8xml_err]%s" % e)
        return res_dict
    for item in root:
        res_dict[item.tag] = item.text
    return res_dict