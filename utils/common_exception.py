class CommonException(Exception):
    def __init__(self, message, code=-1,chi_msg="操作失败"):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.code = code
        self.chi_msg = chi_msg

unknown_err = CommonException("unknown_err",10000,"未知错误")
no_login_err = CommonException("no_login_err",10400,"未登录")
req_format_err = CommonException("req_format_err",10401,"请求格式错误")
auth_err = CommonException("auth_err",10402,"认证或权限错误")
dup_err = CommonException("dup_err",10403,"重复添加")
no_func_err = CommonException("no_func_err",10405,"请求方法不存在错误")
forbid_err = CommonException("forbid_err",10406,"禁止操作")
appinfo_err = CommonException("appinfo_err",10407,"缺少app信息")
req_param_err = CommonException("req_param_err",10408,"请求参数错误")
no_doc_err = CommonException("no_doc_err",10409,"没有符合条件的医生")