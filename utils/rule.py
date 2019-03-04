import functools
from common_lib.utils.common_exception import no_login_err,auth_err,CommonException
from common_lib.utils.utils import get_user_info_by_auth,ret_in_json
from common_lib.common_func import g_stdlogging
import json
# 请求装饰器
def rule_check(rule_list=[]):
    """
请求装饰器
    :param rule_list: [
        {
            "cate":"login",
            "allow_user_type_list":[] ,//若为空，则代表任何用户类型都允许
        },
    ]
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                ins = RuleHandler()
                for rule in rule_list:
                    ins.check(rule)
                res = func(*args, **kwargs)
                return res
            except CommonException as ce:
                g_stdlogging.exception("[rule_check]%s" % ce)
                # if ce.code == 10400:
                #     the_res = {
                #         "error": "invalid_token",
                #         "error_description": "Access token expired: eyxxxx"
                #     }
                #     return json.dumps(the_res, indent=4, ensure_ascii=False)
                return ret_in_json(msg=ce.chi_msg,code=ce.code)
            except Exception as e:
                g_stdlogging.exception("[rule_check]%s" % e)
                return ret_in_json(msg="未知错误",code=-1)
        return wrapper
    return decorator

class RuleHandler():
    def __init__(self):
        pass

    def check(self,rule):
        if rule["cate"]=="login":
            auth_res = get_user_info_by_auth()
            if "user_id" not in auth_res:
                raise no_login_err
            if "allow_user_type_list" in rule and rule["allow_user_type_list"]:
                comm_list = list(set(rule["allow_user_type_list"]).intersection(auth_res["authorities"]))
                if not comm_list:
                    raise auth_err

