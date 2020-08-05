#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/6/18 10:56
# @Author  : cbdeng
# @Software: PyCharm
import pickle
from common_lib.db.redis import RedisClient
from common_lib.db.mysql import get_db
from common_lib.common_func import merge_two_dicts
from common_lib.utils.utils import get_ts8dt,get_uniq_list
import datetime

class QueryUtil():
    def __init__(self,flag,ver=4,id_name="id",ex=300,need_cache=True,db=None):
        if db:
            self.db = db
        else:
            self.db = get_db()
        self.rcli = RedisClient().get_cli()
        self.flag = flag
        self.ver = ver
        self.id_name = id_name
        self.need_cache = need_cache
        self.ex = ex

    def make_key(self, tid):
        return str(self.flag) + "|" + str(self.ver) + "|" + str(self.id_name) + "|"  + str(tid)

    def make_1n_key(self, tid):
        return str(self.flag) + "|1n|" + str(self.ver)+ "|" + str(self.id_name)  + "|" + str(tid)

    def del_by_idlist(self,id_list):
        pipe = self.rcli.pipeline(transaction=False)
        for tid in id_list:
            id_key = self.make_key( tid )
            pipe.delete(id_key )
        pipe.execute()

    def del_1n_by_idlist(self,id_list):
        pipe = self.rcli.pipeline(transaction=False)
        for tid in id_list:
            id_key = self.make_1n_key( tid )
            pipe.delete(id_key )
        pipe.execute()

    '''
    只能获取1:1关系的场景
    id_list : [1,12,222]
    sql_tmpl : "select * from t_store where id in (%s)"
    '''
    def mget_by_idlist(self,id_list,sql_tmpl):
        final_dict = {}
        all_list = []
        cache_dict = {}
        db_dict = {}
        id_list = get_uniq_list(id_list)
        if id_list:
            for item in id_list:
                thetype = type(item)
                break
            id_key_list = []
            for tid in id_list:
                id_key = self.make_key( tid )
                id_key_list.append(id_key)
            res_list = [None for i in id_list]
            if self.need_cache:
                res_list = self.rcli.mget(id_key_list)
            db_id_list = []
            for key, item in enumerate(res_list):
                if not item:
                    db_id_list.append(id_list[key])
                else:
                    cache_dict[id_list[key]] = pickle.loads(item)
            if db_id_list:
                db_id_list_str = ",".join([str(i) for i in db_id_list])
                sql = sql_tmpl % (   db_id_list_str,)
                db_dict = self.mget_by_sql(sql)["dict"]
                if self.need_cache:
                    pipe = self.rcli.pipeline(transaction=False)
                    for key, info in db_dict.items():
                        pipe.set(self.make_key(key), pickle.dumps(info), ex=self.ex)
                    pipe.execute()
            all_tables = merge_two_dicts(cache_dict,db_dict)
            for key,item in all_tables.items():
                final_dict[thetype(key)] = item
            for tid in id_list:
                if tid in final_dict:
                    all_list.append(final_dict[tid])
        return {
            "dict":final_dict,
            "list":all_list
        }


    '''
    能获取1:n关系的场景
    id_list : [1,12,222]
    sql_tmpl : "select * from t_a_b_rel where aid in (%s)"
    '''
    def mget_by_idlist_1n(self,id_list,sql_tmpl):
        final_dict = {}
        all_list = []
        cache_dict = {}
        db_dict = {}
        id_list = get_uniq_list(id_list)
        if id_list:
            for item in id_list:
                thetype = type(item)
                break
            id_key_list = []
            for tid in id_list:
                id_key = self.make_1n_key( tid )
                id_key_list.append(id_key)
            res_list = [None for i in id_list]
            if self.need_cache:
                res_list = self.rcli.mget(id_key_list)
            db_id_list = []
            for key, item in enumerate(res_list):
                if not item:
                    db_id_list.append(id_list[key])
                else:
                    cache_dict[id_list[key]] = pickle.loads(item)
            # print(db_id_list,cache_dict)
            cont_dict = {}
            if db_id_list:
                db_id_list_str = ",".join([str(i) for i in db_id_list])
                sql = sql_tmpl % (   db_id_list_str,)
                mid_res = self.mget_by_sql(sql)
                db_info_list = mid_res["list"]
                for item in db_info_list:
                    if item[self.id_name] in cont_dict:
                        cont_dict[item[self.id_name]].append(item)
                    else:
                        cont_dict[item[self.id_name]] = [item]
                if self.need_cache:
                    pipe = self.rcli.pipeline(transaction=False)
                    for key, info in cont_dict.items():
                        pipe.set(self.make_1n_key(key), pickle.dumps(info), ex=self.ex)
                    pipe.execute()
            all_tables = merge_two_dicts(cache_dict,cont_dict)
            for key,item in all_tables.items():
                final_dict[thetype(key)] = item
            for tid in id_list:
                if tid in final_dict:
                    all_list.append(final_dict[tid])
        return {
            "dict":final_dict,
            "list":all_list
        }


    def mget_by_sql(self,sql):
        tdict = {}
        tlist = []
        cursor = self.db.execute_sql(sql)
        for row in cursor.fetchall():
            table = dict()
            for column, value in zip(cursor.description, row):
                column_name = column[0]
                if type(value) == datetime.datetime:
                    value = get_ts8dt(value)
                table[column_name] = value
            tdict[table[self.id_name]] = table
            tlist.append(table)
        return {
            "dict":tdict,
            "list":tlist
        }