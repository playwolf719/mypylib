#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/2/20 14:23
# @Author  : cbdeng
# @Software: PyCharm
from common_lib.common_func import g_stdlogging
import pika
import json
RABBITMQ_USER = "guest"
RABBITMQ_USER_PASSWORD = "playwolf719007"
push_main_queue = "push_main_queue"
push_delay_queue = "push_delay_queue"
t_exchange = 'pushamq.direct'

def send2mq(info,push_type=0,ttl=1):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_USER_PASSWORD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            'localhost', credentials=credentials))
        # Create normal 'Hello World' type channel.
        channel = connection.channel()
        channel.confirm_delivery()
        channel.queue_declare(queue=push_main_queue, durable=True)

        # We need to bind this channel to an exchange, that will be used to transfer
        # messages from our delay queue.
        channel.queue_bind(exchange=t_exchange, queue=push_main_queue)

        # Create our delay channel.
        delay_channel = connection.channel()
        delay_channel.confirm_delivery()

        # This is where we declare the delay, and routing for our delay channel.
        delay_channel.queue_declare(queue=push_delay_queue, durable=True, arguments={
            # 'x-message-ttl' :3000, # Delay until the message is transferred in milliseconds.
            'x-dead-letter-exchange': t_exchange,  # Exchange used to transfer the message from A to B.
            'x-dead-letter-routing-key': push_main_queue  # Name of the queue we want the message transferred to.
        })
        if ttl<=0:
            raise Exception("ttl less than 1")
        pt = pika.BasicProperties(delivery_mode=2, expiration=str(ttl))
        new_info = {"info":json.loads(info),"push_type":push_type}
        g_stdlogging.info("[send2mq] %s %s" % (new_info,ttl))
        res = delay_channel.basic_publish(exchange='',routing_key=push_delay_queue,body=json.dumps(new_info),properties=pt)
    except Exception as e:
        g_stdlogging.error("[send2mq]err %s " % e)


import jpush
from jpush import common
app_key = "8c9af5213d03d37c760b41c8"
master_secret = "7371124d7146eb4ba326810f"
_jpush = jpush.JPush(app_key, master_secret)
# _jpush.set_logging("DEBUG")

def sendPush2all(text):
    push = _jpush.create_push()
    # if you set the logging level to "DEBUG",it will show the debug logging.
    push.audience = jpush.all_
    push.notification = jpush.notification(alert=text)
    push.platform = jpush.all_
    push.message=jpush.message("msg",extras={'img_url':'img_url' })
    try:
        response = push.send()
        g_stdlogging.info("[sendPush2all]%s %s" % (text,response))
    except common.Unauthorized:
        raise common.Unauthorized("Unauthorized")
    except common.APIConnectionException:
        raise common.APIConnectionException("conn error")
    # except common.JPushFailure:
    #     print("JPushFailure")
    # except:
    #     print("Exception")

def sendPush2multi(text,alias_list):
    push = _jpush.create_push()
    alias_dict={"alias": alias_list}

    push.audience = jpush.audience(
        alias_dict
    )

    push.notification = jpush.notification(alert=text,)
    push.platform = jpush.all_
    push.message=jpush.message("msg",extras={'img_url':'img_url' })
    # print(push.payload)
    res = push.send()
    g_stdlogging.info("[send2multi]%s %s %s %s" % (text,push.payload,alias_list,res))