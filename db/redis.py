#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/27 15:26
# @Author  : cbdeng
# @Software: PyCharm
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/17 9:53
# @Author  : cbdeng
# @Software: PyCharm
import redis
from common_lib.utils.conf_util import g_conf
import logging

g_client_dict = {}


class RedisClient():
    def __init__(self, host="", port=""):
        self.config = g_conf
        self.time_out = 0.2
        self.cli = None
        self.host = host
        self.port = port
        if not self.host or not self.port:
            self.host = self.config['redis']['host']
            self.port = int(self.config['redis']['port'])

    def get_key(self):
        return "redis_cli:{}:{}".format(self.host, self.port)

    def make(self):
        global g_conf
        key = self.get_key()
        if key in g_client_dict and g_client_dict[key]:
            self.cli = g_client_dict[key]
        else:
            self.config = g_conf
            self.time_out = 0.2
            if not self.host or not self.port:
                self.host = self.config['redis']['host']
                self.port = int(self.config['redis']['port'])
            key = self.get_key()
            rdp = redis.ConnectionPool(host=self.host, port=self.port,)
            rdc = redis.Redis(connection_pool=rdp,socket_connect_timeout=self.time_out,retry_on_timeout=self.time_out,socket_timeout=self.time_out)
            g_client_dict[key] = rdc
            self.cli = rdc

    def get_cli(self):
        try:
            self.make()
        except Exception as e:
            logging.error("[RedisClient]%s" % (e))
        return self.cli

    def destroy(self):
        key = self.get_key()
        if key in g_client_dict:
            g_client_dict[key] = None