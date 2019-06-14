#!/usr/bin python
# -*- coding: UTF-8 -*-
# filename:  asset_main.py
# creator:   jacob.qian
# datetime:  2013-5-31
# Ronaldo wokers类的基类
import json

import logging
import urllib

#import time
import logging.config
logging.config.fileConfig("/opt/Keeprapid/OpenApiRonaldo/server/conf/log.conf")
logr = logging.getLogger('ronaldo')





class WorkerBase():

    ERROR_RSP_UNKOWN_COMMAND = '{"seq_id":"123456","body":{},"errcode":"40000","errmsg":"unkown msg"}'
    #errorcode define
    ERRORCODE_OK = "200"
    ERRORCODE_UNKOWN_CMD = "40000"
    ERRORCODE_SERVER_ABNORMAL = "40001"
    ERRORCODE_URL_HAS_INVALID_PARAM = '40002'
    ERRORCODE_DB_ERROR = '40003'
    ERRORCODE_INVALID_URL = '40004'
    ERRORCODE_CMD_HAS_INVALID_PARAM = '40005'

    ERRORCODE_DEVELOPER_NOT_EXIST = '41001'
    ERRORCODE_MEMBER_PASSWORD_INVALID = '41002'
    ERRORCODE_APPID_OR_SECRET_INVALID = '41003'
    ERRORCODE_DESTURL_AUTH_FAILED = '41004'
    ERRORCODE_ACCESSTOKEN_INVALID = '41005'
    ERRORCODE_ACCESSTOKEN_OOS = '41006'
    ERRORCODE_MEMBER_NOT_EXIST = '41007'
    ERRORCODE_MEMBER_NOT_BELONGS = '41008'
    ERRORCODE_VID_ERROR = '41009'
    ERRORCODE_MEMBER_USERNAME_ALREADY_EXIST = '41010'
    ERRORCODE_BUNDLEID_ERROR = '41011'

    #member_state
    DEVELOPER_STATE_INIT = 0
    DEVELOPER_STATE_ACTIVE = 1

    #email validate
    DEVELOPER_EMAIL_STATE_INIT = 0
    DEVELOPER_EMAIL_STATE_COMFIRM = 1

    #interface 
    INTERFACE_STATE_CLOSE = 0
    INTERFACE_STATE_TEST = 1
    INTERFACE_STATE_AUTHORIZE = 2

    MEMBER_TYPE_NORMAL = 0
    MEMBER_TYPE_TALENT = 1
    #增加FOLLOW权限
    MEMBER_FOLLOW_ROLE_NORMAL = 0
    MEMBER_FOLLOW_ROLE_REFUES = 1
    #SHARE 权限
    MEMBER_SHARE_YES = 1
    MEMBER_SHARE_NO = 0

    BODYFUNCTION_TYPE_HEARTRATE = 1
    BODYFUNCTION_TYPE_WEIGHT = 2
    BODYFUNCTION_TYPE_HEIGHT = 3
    BODYFUNCTION_TYPE_BLOODPRESS = 4
    BODYFUNCTION_TYPE_BMI = 5
    BODYFUNCTION_TYPE_BLOODSUGAR = 6
    BODYFUNCTION_TYPE_BLOODLIPID = 7
    BODYFUNCTION_TYPE_BODYFATPERCENT = 8
    BODYFUNCTION_TYPE_BLOODFATMASS = 9
    BODYFUNCTION_TYPE_BLOODFREEMASS = 10


    MEMBER_PASSWORD_VERIFY_CODE = "abcdef"

    #notify type
    NOTIFY_TYPE_GETBACKPASSWORD = 'GetBackPassword'
    NOTIFY_TYPE_GETBACKPASSWORD_YOO = 'GetBackPassword_yoo'
    NOTIFY_TYPE_GETBACKPASSWORD_INTEX = 'GetBackPassword_intex'
    #redis
    #maxauthcount key
    KEY_TOKEN = "R:tid:%s"
    KEY_DEVELOPERID = "R:di:%s"
    KEY_VID = "R:v:%s"
    KEY_ACCESSTOKEN = "R:act:%s"
    
    #email
    SEND_EMAIL_INTERVAL = 2

    USER_SOURCE_ORIGIN = "origin"
    USER_SOURCE_FACEBOOK = "facebook"


    PASSWORD_GEAR_DEL = "jtwmydtsgx"

    TOKEN_EXPIRE_TIME = 15*24*60*60
    ACCESSTOKEN_EXPIRE_TIME = 15*24*60*60

    DATA_TYPE_FITNESS = "fitness"
    DATA_TYPE_SLEEP = "sleep"
    DATA_TYPE_BODYFUNCTION = "bodyfunction"
    DATA_TYPE_TRAINING = "training"
    DATA_TYPE_TRAININGDETAIL = "trainingdetail"
    DATA_TYPE_SUMMARY = "summary "

    DATA_UPLOAD_MAXCOUNT = 500
    DATA_DOWNLOAD_MAXCOUNT = 100

    VID_IRK = '000001001001'
    VID_KRWATCH = '000001001002'
    VID_WANNAFIT = '000004001004'
    VID_SGEAR = '000004001002'
    VID_ORACOM = '000004001001'
    VID_FJFIT = '000004001003'
    VID_OBANGLE = '000005001001'
    VID_POLARID = '000005001002'
    VID_FITBAND = '000006001001'
    VID_RTCO = '000006001002'
    VID_JEEP = '000006001003'
    VID_FYTPRIME = '000006001004'
    VID_HEMA = '000006001005'
    VID_CHOMPFIT = '00000F001001'
    VID_YOO = '00000F001002'
    VID_TRAKFIT = '00000F001004'
    VID_LAFIT = '00000F001005'
    VID_WELLFIT = '00000F001006'
    VID_ALT = '00000F001007'
    VID_POWERSENOR = '000010001001'
    VID_SMARTWATCH = '000010001002'
    VID_TOUCHBAND = '000010001003'
    VID_SPRINGBAND = '000010001004'
    VID_GOBAND = '000012001001'
    VID_YOURFITNESSTRACKER = '000012001002'
    VID_FITRIST = '000012001003'
    VID_FITRISTPUZZLE = '000012001006'
    VID_HAIR = '000012001007'
    VID_GEBIYA = '000012001008'
    VID_CZJK_FITGO = '000012001009'
    VID_GETFIT = '000012001010'
    VID_HCBRACELET = '000014001001'

    MEMBERLIST_MAX_COUNT = 10000
    #校验SDK合法性超时（小时）
    VALIDATE_SDK_TIMEOUT = 24

    def __init__(self, moduleid):
        try:
            logr.debug('WorkerBase::__init__')
            self._moduleid = moduleid
            fileobj = open('/opt/Keeprapid/OpenApiRonaldo/server/conf/db.conf', 'r')
            self._json_dbcfg = json.load(fileobj)
            fileobj.close()

            fileobj = open('/opt/Keeprapid/OpenApiRonaldo/server/conf/config.conf', 'r')
            self._config = json.load(fileobj)
            fileobj.close()

            fileobj = open('/opt/Keeprapid/OpenApiRonaldo/server/conf/errmsg.conf', 'r')
            self._errmsg = json.load(fileobj)
            fileobj.close()

#            fileobj = open('/opt/Keeprapid/Ronaldo/server/conf/vid.conf', 'r')
#            self._vidconfig = json.load(fileobj)
#            fileobj.close()

            self._redis = None
            
        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))

    def redisdelete(self, argslist):
        logger.debug('%s' % ('","'.join(argslist)))
        ret = eval('self._redis.delete("%s")'%('","'.join(argslist)))
        logger.debug('delete ret = %d' % (ret))

    def _sendMessage(self, to, body):
        #发送消息到routkey，没有返回reply_to,单向消息
#        logger.debug(to +':'+body)
        if to is None or to == '' or body is None or body == '':
            return

        self._redis.lpush(to, body)


    def _getvalueinlistdict(self, request_key, condition_key, condition_value, d):
        for k in d:
            if request_key not in k or condition_key not in k:
                continue
            if k[condition_key] == condition_value:
                return k[request_key]

        return None

    def _setvalueinlistdict(self, request_key, request_value, condition_key, condition_value, d):
        for k in d:
            if request_key not in k or condition_key not in k:
                continue
            if k[condition_key] == condition_value:
                k[request_key] = request_value
                return True

        return False

    def _getobjinlistdict(self, condition_key, condition_value, d):
        for k in d:
            if condition_key not in k:
                continue
            if k[condition_key] == condition_value:
                return k

        return None
        
    def _findvalueinlistdict(self, key, value, d):
        for k in d:
            if key not in k:
                continue
            if k[key] == value:
                return True

        return False

    def _makeclientbodys(self, action_name, action_version, paramsdict=dict(), invoke_id=None, categroy=None, user_agent=None):
        
        actiondict = dict({'body':paramsdict})
#        if invoke_id is None:
#            clientdict['id'] = invoke_id
#        else:
#            clientdict['id'] = self._ident
#
#        if categroy is None:
#            clientdict['categroy'] = 'SERVER'
#        else:
#            clientdict['categroy'] = categroy
#
#        if user_agent is None:
#            clientdict['user_agent'] = 'python'
#        else:
#            clientdict['user_agent'] = categroy

        actiondict['action_cmd'] = action_name
        actiondict['version'] = action_version
        actiondict['seq_id'] = str(random.randint(1,100000000))
#        logr.debug(actiondict)

        return json.dumps(actiondict)

    def _getvaluefromactionresponse(self, request_key, ret, content):
#        if 'status'in ret and ret['status'] == '200':
        try:
            if content is not None:
                contentxml = xmltodict.parse(content)
                return contentxml.get('server').get('action').get(request_key)
        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            return "UNKOWN"


    def _sendhttpaction(self, module_key, action_name, action_version, action_paramdict):
        bodys = self._makeclientbodys(action_name, action_version, action_paramdict)
        obj = sendhttppost.SendHttpPostRequest()
        ret,content = obj.sendhttprequest(module_key,bodys)
        errorcode = self._getvaluefromactionresponse('errorcode', ret, content)
        return errorcode, ret, content

    def _sendhttpaction2(self, ip, port, module_key, action_name, action_version, action_paramdict):
        bodys = self._makeclientbodys(action_name, action_version, action_paramdict)
        obj = sendhttppost.SendHttpPostRequest()
        ret,content = obj.sendhttprequest2(ip, port, module_key,bodys)
        errorcode = self._getvaluefromactionresponse('errorcode', ret, content)
        return errorcode, ret, content

    #递归调用，解析每一层可能需要urllib.unquote的地方
    def parse_param_lowlevel(self, obj):
        if isinstance(obj,dict):
            a =dict()
            for key in obj:
                if isinstance(obj[key],dict) or isinstance(obj[key],list):
                    a[key] = self.parse_param_lowlevel(obj[key])
                elif isinstance(obj[key],unicode) or isinstance(obj[key],str):
                    a[key] = urllib.unquote(obj[key].encode('utf-8')).decode('utf-8')
                else:
                    a[key] = obj[key]
            return a
        elif isinstance(obj,list):
            b = list()
            for l in obj:
                if isinstance(l, dict) or isinstance(l, list):
                    b.append(self.parse_param_lowlevel(l))
                elif isinstance(l,unicode) or isinstance(l,str):
                    b.append(urllib.unquote(l.encode('utf-8')).decode('utf-8'))
                else:
                    b.append(l)
            return b
        elif isinstance(obj,unicode) or isinstance(obj,str):
            return urllib.unquote(obj.encode('utf-8')).decode('utf-8')
        else:
            return obj

    #递归调用，解析每一层可能需要urllib.unquote的地方
    def packet_param_lowlevel(self, obj):
        if isinstance(obj,dict):
            a =dict()
            for key in obj:
                if isinstance(obj[key],dict) or isinstance(obj[key],list):
                    a[key] = self.packet_param_lowlevel(obj[key])
                elif isinstance(obj[key],unicode) or isinstance(obj[key],str):
                    a[key] = urllib.quote(obj[key].encode('utf-8'))
                else:
                    a[key] = obj[key]
            return a
        elif isinstance(obj,list):
            b = list()
            for l in obj:
                if isinstance(l, dict) or isinstance(l, list):
                    b.append(self.packet_param_lowlevel(l))
                elif isinstance(l,unicode) or isinstance(l,str):
                    b.append(urllib.quote(l.encode('utf-8')))
                else:
                    b.append(l)
            return b
        elif isinstance(obj,unicode) or isinstance(obj,str):
            return urllib.quote(obj.encode('utf-8'))
        else:
            return obj


    def printplus(self, obj):
        # Dict
        logr.debug("===============begin dump============== ")
        if isinstance(obj, dict):
            for k, v in sorted(obj.items()):
                logr.debug(u'{0}: {1}'.format(k, v))

        # List or tuple            
        elif isinstance(obj, list) or isinstance(obj, tuple):
            for x in obj:
                logr.debug(x)

        # Other
        else:
            logr.debug(obj)
        logr.debug("===============end dump============== ")
    #///////////////////for Ronaldo only////////////////////////////////
 

