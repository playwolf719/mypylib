#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/12/10 14:04
# @Author  : cbdeng
# @Software: PyCharm
from datetime import datetime
from peewee import SQL,DateTimeField
import time
from common_lib.db.mysql import get_db
from common_lib.common_func import g_mylogging
from common_lib.utils.utils import get_dtstr_by_ts
from common_lib.utils.common_exception import no_login_err,dup_err,auth_err,req_format_err,no_func_err,forbid_err
from playhouse.shortcuts import model_to_dict
from common_lib.db.mysql import mu_catch
from common_lib.utils.utils import is_date
logging = g_mylogging

oper_list = ["query","insert","update","delete"]
import json
g_test = 0

class MysqlUtil():
    def __init__(self,db_dict,dt_trans=True,admin_end=True):
        if type(db_dict) is not dict:
            raise Exception("[MysqlUtil]init_dict must be dict")
        self.db_dict = db_dict
        self.dt_trans = dt_trans
        self.admin_end = admin_end

    def handler(self,input_dict):
        # flag
        self.self_check_flag = False
        self.uinfo_res = None
        self.input_dict = input_dict
        if not all(k in self.input_dict for k in ("ent", "oper","info") ):
            raise Exception("[MysqlUtil] input_dict key err")
        if self.input_dict["ent"] not in self.db_dict:
            raise Exception("[MysqlUtil]ent err")
        self.Ins = self.db_dict[self.input_dict["ent"]]["model"]
        self.ent_dict = self.db_dict[self.input_dict["ent"]]
        self.before_handler()
        res = self.mid_handler()
        self.after_handler()
        return res

    @mu_catch()
    def mid_handler(self):
        # global g_test
        # if g_test == 0:
        #     g_test = g_test + 1
        #     raise Exception("fuck")
        invert_op = getattr(self.Ins, "ct_" + self.input_dict["oper"], None)
        if callable(invert_op):
            res = invert_op(self)
        else:
            if self.input_dict["oper"] in oper_list:
                comm_op = getattr(self, self.input_dict["oper"])
                if callable(comm_op):
                    res = comm_op()
                else:
                    raise no_func_err
            else:
                raise no_func_err
        return res


    def before_handler(self):
        self.appver = self.input_dict["info"].pop("appver",0)
        self.dp = self.input_dict["info"].pop("dp","")
        if "forbid_oper_list" in self.ent_dict and self.ent_dict["forbid_oper_list"] and self.input_dict["oper"] in self.ent_dict["forbid_oper_list"]:
            raise forbid_err

        if "uinfo_func" in self.db_dict:
            self.uinfo_res = self.db_dict["uinfo_func"]()
            if ("auth_oper_list" not in self.ent_dict or not self.ent_dict["auth_oper_list"]):
                if not self.uinfo_res:
                    raise no_login_err
            else:
                the_err = None
                for item in self.ent_dict["auth_oper_list"]:
                    if item["oper_list"] == "all" or self.input_dict["oper"] in item["oper_list"]:
                        if "need_auth" in item and not item["need_auth"]:
                            the_err = None
                            break
                        if not self.uinfo_res:
                            raise no_login_err
                        if "user_cate" in item:
                            if list(set(self.uinfo_res[self.db_dict["uinfo_cate_field"]]).intersection(item["user_cate"])):
                                if "self_check" in item and item["self_check"]:
                                    self.self_check_flag = True
                                else:
                                    self.self_check_flag = False
                                the_err = None
                            else:
                                the_err = auth_err
                    else:
                        if not self.uinfo_res:
                            raise no_login_err

                if the_err:
                    raise the_err
        if "before_rule_list" in self.ent_dict:
            for item in self.ent_dict["before_rule_list"]:
                if self.input_dict["oper"] in item["oper_fit_list"]:
                    if "before_handler" in item:
                        self.input_dict["info"] = item["before_handler"](self.input_dict["info"])

    def after_handler(self):
        if "after_rule_list" in self.ent_dict:
            for item in self.ent_dict["after_rule_list"]:
                if self.input_dict["oper"] in item["oper_fit_list"]:
                    if "after_handler" in item:
                        res = item["after_handler"](self.input_dict["info"])

    def query(self):
        info_dict = self.input_dict["info"]
        index = 0
        count = 10
        offset = 0

        final_res = {
            "data_list": [],
            "offset": offset,
            "count": count,
            "cur_page": 0,
            "total_page": 0,
            "this_count": 0,
            "total_count": 0,
        }
        if "count" in info_dict and info_dict["count"]<=100:
            count = info_dict["count"]
        if "offset" in info_dict:
            offset = info_dict["offset"]
        final_res["count"] = count
        final_res["offset"] = offset
        sql = info_dict.pop("sql",None)
        count_sql = info_dict.pop("count_sql",None)
        if sql and not count_sql or not sql and count_sql:
            raise req_format_err
        if not sql or not count_sql:
            #  field
            if "field" in info_dict:
                f_list = []
                for field in info_dict["field"]:
                    attr = getattr(self.Ins, field)
                    f_list.append(attr)
                myquery = self.Ins.select(*f_list)
            else:
                myquery = self.Ins.select()
            # where
            if self.admin_end:
                sql_where = ""
                if "where" in info_dict:
                    sql_where = info_dict["where"]
                if self.self_check_flag:
                    q1 = " %s = %s" % (self.ent_dict["uid_name"],self.uinfo_res["id"])
                    if sql_where:
                        sql_where = sql_where + " and %s " % q1
                    else:
                        sql_where = q1
                if sql_where:
                    myquery = myquery.where(SQL('%s' % sql_where))
            final_res["total_count"] = myquery.count()
            if "order_by" in info_dict:
                for item in info_dict["order_by"]:
                    attr = getattr(self.Ins,item["field"])
                    myquery = myquery.order_by(getattr(attr,item["sort"])())
            myquery = myquery.offset(offset).limit(count).dicts()
            for item in myquery:
                tmp_dict = item
                # dt_trans
                if self.dt_trans:
                    for key, item1 in tmp_dict.items():
                        if type(item1) == datetime:
                            tmp_dict[key] = int(time.mktime(item1.timetuple()))
                final_res["data_list"].append(tmp_dict)
                index += 1
        elif sql and count_sql:
            db = get_db()
            if self.admin_end:
                if "where" in info_dict:
                    sql = sql + " where " + info_dict["where"]
            if "order_by" in info_dict and info_dict["order_by"]:
                sql = sql + " order by "
                for item in info_dict["order_by"]:
                    sql = sql+ " " +item["field"] + " " + item["sort"]
            res = db.execute_sql(count_sql)
            final_res["total_count"] = res.fetchone()[0]
            sql = sql + " limit %s,%s" % (offset,count)
            cursor = db.execute_sql(sql)
            db.close()
            field_list = []
            if "field" in info_dict:
                field_list = info_dict["field"]
            for row in cursor.fetchall():
                index += 1
                if field_list and len(row)!=len(field_list):
                    raise req_format_err
                tmp = {}
                if field_list:
                    for key,item in enumerate(field_list):
                        tmp[item] = row[key]
                else:
                    for key,item in enumerate(row):
                        tmp[key] = row[key]
                final_res["data_list"].append(tmp)
        else:
            raise req_format_err
        #  count
        final_res["this_count"] = index
        final_res["cur_page"] = int(offset/count)+1
        if final_res["total_count"] % count == 0 and final_res["total_count"]!=0:
            tp = int(final_res["total_count"]/count)
        else:
            tp = int(final_res["total_count"]/count)+1
        final_res["total_page"] = tp
        return final_res

    def insert(self):
        flag = None
        info_dict = self.input_dict["info"]
        db = get_db()
        try:
            # for item in info_dict["ct_param"]:
            #     if item["key"] in info_dict:
            #         if item["handle"] == "jsondump":
            #             info_dict[item["key"]] = json.dumps(info_dict[info_dict[item["key"]]])
            info_dict.pop('ct_param', None)
            ct_field = info_dict.pop('ct_field', None)
            for key,item in self.Ins._meta.fields.items():
                if type(item) == DateTimeField:
                    if key not in info_dict:
                        info_dict[key] = get_dtstr_by_ts()
            flag,created = self.Ins.get_or_create(**info_dict)
            # for key,item in self.Ins._meta.fields.items():
            #     val = getattr(flag,key)
            #     print(type(val))
            flag = model_to_dict(flag)
            for key,item in flag.items():
                if key in ["update_time","create_time"]:
                    flag[key] = int(time.mktime(datetime.strptime(item, "%Y-%m-%d %H:%M:%S").timetuple()))
            tmp = {}
            if ct_field:
                for key,item in flag.items():
                    if key in ct_field:
                        tmp[key] = item
                flag = tmp
        except Exception as e:
            if "Duplicate" in str(e):
                raise dup_err
            else:
                logging.exception("[insert]%s" % e)
            db.rollback()
        return flag

    def update(self):
        info_dict = self.input_dict["info"]
        # pk_field = "id"
        # if "pk" in info_dict:
        #     pk_field =info_dict["pk"]
        # pk_val =info_dict["pk_val"]
        # Ins_pk = getattr(self.Ins,pk_field)
        flag =None
        cond = info_dict.pop('where', None)

        db = get_db()
        if self.self_check_flag:
            q1 = " %s = %s" % (self.ent_dict["uid_name"], self.uinfo_res["id"])
            if cond:
                cond = cond + " and %s " % q1
            else:
                cond = q1
        try:
            flag = self.Ins.update(**info_dict).where(SQL(' %s ' % cond)).execute()
            if self.self_check_flag and not flag:
                raise auth_err
        except Exception as e:
            logging.exception("[update]%s" % e)
            db.rollback()
        return flag


    def delete(self):
        info_dict = self.input_dict["info"]
        pk_field = "id"
        if "pk" in info_dict:
            pk_field =info_dict["pk"]
        pk_val =info_dict["pk_val"]
        Ins_pk = getattr(self.Ins,pk_field)
        info_dict.pop("pk",None)
        info_dict.pop("pk_val",None)
        num =0
        db = get_db()
        try:
            myquery = self.Ins.delete().where(Ins_pk==pk_val)
            if self.self_check_flag:
                uid_field = getattr(self.Ins, self.ent_dict["uid_name"])
                myquery = myquery.where(uid_field==self.uinfo_res["id"])
            num = myquery.execute()
            if self.self_check_flag and not num:
                raise auth_err
        except Exception as e:
            logging.exception("[delete]%s" % e)
            db.rollback()
        return num
