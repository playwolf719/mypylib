#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/4/9 9:51
# @Author  : cbdeng
# @Software: PyCharm
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import time


def send_email( mail_title,econtent,receiver_list):
    # 第三方 SMTP 服务
    host_server = 'smtp.qq.com'
    # host_server = 'smtp.mxhichina.com'
    # sender_qq为发件人的qq号码
    # 真实的发送邮箱
    sender_qq = '249583905@qq.com'
    # pwd为qq邮箱的授权码
    pwd = 'cznbgkmufbtgcbcd'  #qq
    # 发件人的邮箱
    # sender_mail = 'sznlp_qa@163.com'
    # 展示的发送邮箱
    sender_mail = sender_qq
    # 收件人邮箱
    receivers = receiver_list

    # 邮件的正文内容
    mail_content = econtent

    # ssl登录
    smtp = SMTP_SSL(host_server)
    # set_debuglevel()是用来调试的。参数值为1表示开启调试模式，参数值为0关闭调试模式
    # smtp.set_debuglevel(1)
    smtp.ehlo(host_server)
    smtp.login(sender_qq, pwd)

    msg = MIMEText(mail_content, "html", 'utf-8')
    # msg = MIMEText(body, format, 'utf-8')
    msg["Accept-Language"] = "zh-CN"
    msg["Accept-Charset"] = "ISO-8859-1,utf-8"
    msg["Subject"] = Header(mail_title, 'utf-8')
    # msg["From"] = Header('Healoonow','utf-8')
    msg["From"] = receiver_list[0]
    msg["To"] = ",".join(receiver_list)
    # msg["To"] = Header("QA工作组", 'utf-8')  ## 接收者的别名

    smtp.sendmail(sender_mail, receivers, msg.as_string())
    smtp.quit()

send_email("test","test",["playwolf719@163.com"])