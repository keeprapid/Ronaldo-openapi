#!/usr/bin python
# -*- coding: UTF-8 -*-
# filename:  gearcenter_worker.py
# creator:   jacob.qian
# datetime:  2013-5-31
# Ronaldo gearcenter 工作线程

import sys
import subprocess
import os
import time
import datetime
import time
import threading

if '/opt/Keeprapid/OpenApiRonaldo/server/apps/common' not in sys.path:
    sys.path.append('/opt/Keeprapid/OpenApiRonaldo/server/apps/common')
import workers
import redis
import json
import pymongo

import logging
import logging.config
import uuid
import random
import urllib
import hashlib
import socket
import httplib2
import string

from bson.objectid import ObjectId

logging.config.fileConfig("/opt/Keeprapid/OpenApiRonaldo/server/conf/log.conf")
logr = logging.getLogger('ronaldo')


class Developer(threading.Thread, workers.WorkerBase):

    def __init__(self, moduleid):
        logr.debug("Developer :running in __init__")
        threading.Thread.__init__(self)
        workers.WorkerBase.__init__(self, moduleid)
#        self.mongoconn = pymongo.Connection(self._json_dbcfg['mongo_ip'],int(self._json_dbcfg['mongo_port']))
        self.mongoconn = pymongo.MongoClient('mongodb://%s:%s@%s:%s/' % (self._json_dbcfg['master_dbuser'],self._json_dbcfg['master_dbpwd'],self._json_dbcfg['master_dbip'],self._json_dbcfg['master_dbport']))
#        self._redis = redis.StrictRedis(self._json_dbcfg['redisip'], int(self._json_dbcfg['redisport']))
        self.db = self.mongoconn.openapi
        self.col_developer = self.db.developer
        self.col_developer_oplog = self.db.oplog
        self.col_applist = self.db.applist
        

        self.thread_index = moduleid
        self._redis = redis.StrictRedis(self._json_dbcfg['local_redisip'], int(self._json_dbcfg['local_redisport']),password=self._json_dbcfg['local_redispassword'])
        self.recv_queue_name = "W:Queue:Developer"
        if 'developer' in self._config:
            if 'Consumer_Queue_Name' in _config['developer']:
                self.recv_queue_name = _config['developer']['Consumer_Queue_Name']


    def __str__(self):
        pass
        '''

        '''

    def _proc_message(self, recvbuf):
        '''消息处理入口函数'''
        # logr.debug('_proc_message')
        #解body
        msgdict = dict()
        try:
            logr.debug(recvbuf)
            msgdict = json.loads(recvbuf)
        except:
            logr.error("parse body error")
            return
        #检查消息必选项
        if len(msgdict) == 0:
            logr.error("body lenght is zero")
            return
        if "from" not in msgdict:
            logr.error("no route in body")
            return
        msgfrom = msgdict['from']

        seqid = '0'
        if "seqid" in msgdict:
            seqid = msgdict['seqid']

        sockid = ''
        if 'sockid' in msgdict:
            sockid = msgdict['sockid']

        if "action_cmd" not in msgdict:
            logr.error("no action_cmd in msg")
            self._sendMessage(msgfrom, '{"from":%s,"errcode":"40000","errmsg":%s,"seq_id":%s,"body":{},"sockid":%s}' % (self.recv_queue_name, self._errmsg.get('40000'), seqid, sockid))
            return
        #构建回应消息结构
        action_cmd = msgdict['action_cmd']

        message_resp_dict = dict()
        message_resp_dict['from'] = self.recv_queue_name
        message_resp_dict['seq_id'] = seqid
        message_resp_dict['sockid'] = sockid
        message_resp_body = dict()
        message_resp_dict['body'] = message_resp_body
        
        self._proc_action(msgdict, message_resp_dict, message_resp_body)

        msg_resp = json.dumps(message_resp_dict)
        logr.debug(msg_resp)
        self._sendMessage(msgfrom, msg_resp)   

    def _proc_action(self, msg_in, msg_out_head, msg_out_body):
        '''action处理入口函数'''
        if 'action_cmd' not in msg_in or 'version' not in msg_in:
            logr.error("mandotry param error in action")
            msg_out_head['errcode'] = '40002'
            msg_out_head['errmsg'] = self._errmsg.get('40002')
            return
        action_cmd = msg_in['action_cmd']
        logr.debug('action_cmd : %s' % (action_cmd))
        action_version = msg_in['version']
        # logr.debug('action_version : %s' % (action_version))
        if 'body' in msg_in:
            action_body = msg_in['body']
#            logr.debug('action_body : %s' % (action_body))
        else:
            action_body = None
            logr.debug('no action_body')

        if action_cmd == 'register':
            self._proc_action_register(action_version, action_body, msg_out_head, msg_out_body)
        elif action_cmd == 'login':
            self._proc_action_login(action_version, action_body, msg_out_head, msg_out_body)
        elif action_cmd == 'update':
            self._proc_action_update(action_version, action_body, msg_out_head, msg_out_body)
        elif action_cmd == 'auth_url':
            self._proc_action_auth_url(action_version, action_body, msg_out_head, msg_out_body)
        elif action_cmd == 'update_vid':
            self._proc_action_update_vid(action_version, action_body, msg_out_head, msg_out_body)
        elif action_cmd == 'validate_sdk':
            self._proc_action_validate_sdk(action_version, action_body, msg_out_head, msg_out_body)            
        else:
            msg_out_head['errcode'] = self.ERRORCODE_UNKOWN_CMD
            msg_out_head['errmsg'] = self._errmsg.get(self.ERRORCODE_UNKOWN_CMD)
        return
 

    def start_forever(self):
        logr.debug("running in start_forever")
        self._start_consumer()

    def calcpassword(self, password, verifycode):
        m0 = hashlib.md5(verifycode)
#        logr.debug("m0 = %s" % m0.hexdigest())
        m1 = hashlib.md5(password + m0.hexdigest())
    #        print m1.hexdigest()
#        logr.debug("m1 = %s" % m1.hexdigest())
        md5password = m1.hexdigest()
        return md5password

    def generator_tokenid(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(60))

    def redisdelete(self, argslist):
        logr.debug('%s' % ('","'.join(argslist)))
        ret = eval('self._redis.delete("%s")'%('","'.join(argslist)))
        logr.debug('delete ret = %d' % (ret))


    def run(self):
        logr.debug("Start Developer pid=%s, threadindex = %s" % (os.getpid(),self.thread_index))
#        try:
        if 1:
            while 1:
                recvdata = self._redis.brpop(self.recv_queue_name)
                t1 = time.time()
                if recvdata:
                    self._proc_message(recvdata[1])
                # logr.debug("_proc_message cost %f" % (time.time()-t1))                    

    def collect_developer_oplog(self, developerid, username, optype, operid, opername, extra):
        insertdevicelog = dict()

        #添加登陆记录
        insertlog = dict({\
            'developerid':developerid,\
            'username':username,\
            'optype':optype,\
            'operid':operid,\
            'opername': opername,\
            'timestamp': datetime.datetime.now(),\
            'timet':time.time()\
            })
        if extra is not None and len(extra)>0:
            insertlog.update(extra)

        self.col_developer_oplog.insert_one(insertlog)
        return

    def makeAppId(self):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))

    def makeSecret(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(40))


    def _proc_action_register(self, version, action_body, retdict, retbody):
        '''
        input : {    'action_cmd'  : 'gear_add', M
                     'seq_id      : M
                     'version'    : M
                     'body'   :{
                        'to'    : M
                        'content'     : M
                        'carrier'     : M
                        'notify_type'   : M
                        
                    }
                }

        output:{   
                   'errcode       : "200"'
                   'seq_id'         : M
                }
        '''
        logr.debug(" into _proc_action_register action_body:%s"%action_body)
        try:
#        if 1:
            
            if ('username' not in action_body) or  ('password' not in action_body) :
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['username'] is None or action_body['password'] is None :
                retdict['errcode'] = self.ERRORCODE_MEMBER_PASSWORD_INVALID
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            username = urllib.unquote(action_body['username'].encode('utf-8')).decode('utf-8')
            username = username.lower()
            username = username.replace(' ','')
            nickname = username

            tmpinsertdict = dict()
            tmpinsertdict.update(action_body)
            tmpinsertdict.pop('username')
            tmpinsertdict.pop('password')
            insertdict = self.parse_param_lowlevel(tmpinsertdict)
            insertdict['username'] = username
            insertdict['password'] = self.calcpassword(action_body['password'],self.MEMBER_PASSWORD_VERIFY_CODE)
            insertdict['state'] = self.DEVELOPER_STATE_INIT
            insertdict['memberinfo_interface_auth'] = self.INTERFACE_STATE_CLOSE
            insertdict['data_interface_auth'] = self.INTERFACE_STATE_CLOSE
            insertdict['push_interface_auth'] = self.INTERFACE_STATE_CLOSE
            insertdict['email_validate'] = self.DEVELOPER_EMAIL_STATE_INIT
            insertdict['create_time'] = datetime.datetime.now()
            insertdict['update_time'] = None
            insertdict['confirm_time'] = None
            insertdict['appid'] = self.makeAppId()
            insertdict['secret'] = self.makeSecret()
            insertdict['vidlist'] = list()
            if 'dest_url' not in insertdict:
                insertdict['dest_url'] = ''
            logr.debug(insertdict)


            developerinfo = self.col_developer.find_one({'username': username})
            if developerinfo is None:                
                objid = self.col_developer.insert_one(insertdict)
                developerid = objid.inserted_id.__str__()
                retdict['errcode'] = self.ERRORCODE_OK
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
                retdict['developerid'] = developerid
                self.collect_developer_oplog(developerid, username, 'register', developerid, username, dict())
            else:
                retdict['errcode'] = self.ERRORCODE_MEMBER_USERNAME_ALREADY_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_MEMBER_USERNAME_ALREADY_EXIST)
            
            
            return

        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            retdict['errcode'] = self.ERRORCODE_SERVER_ABNORMAL
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_SERVER_ABNORMAL)

    def _proc_action_login(self, version, action_body, retdict, retbody):
        '''
        input : {    'action_cmd'  : 'gear_add', M
                     'seq_id      : M
                     'version'    : M
                     'body'   :{
                        'to'    : M
                        'content'     : M
                        'carrier'     : M
                        'notify_type'   : M
                        
                    }
                }

        output:{   
                   'errcode       : "200"'
                   'seq_id'         : M
                }
        '''
        logr.debug(" into _proc_action_login action_body:%s"%action_body)
        try:
#        if 1:
            
            if ('username' not in action_body) or  ('password' not in action_body):
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            if action_body['password'] is None or action_body['password'] == '':
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['username'] is None or action_body['username'] == '':
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            username = urllib.unquote(action_body['username'].encode('utf-8')).decode('utf-8')
            username = username.lower()
            username = username.replace(' ','')

            tokenid = None
            developerid = ''
            logr.debug(username)
            developerinfo = self.col_developer.find_one({'username': username})
            if developerinfo is None:
                retdict['errcode'] = self.ERRORCODE_DEVELOPER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DEVELOPER_NOT_EXIST)
                return

            if action_body['password'] != developerinfo['password']:
                retdict['errcode'] = self.ERRORCODE_MEMBER_PASSWORD_INVALID
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_MEMBER_PASSWORD_INVALID)
                return
            developerid = developerinfo['_id'].__str__()
#            logr.debug("key = %s" % searchkey)
            developerinfokey = self.KEY_DEVELOPERID % (developerinfo['_id'].__str__())
#            if self._redis.exists(developerinfokey) is False:
            developerinfo_redis = dict()
            developerinfo_redis.update(developerinfo)
            developerinfo_redis['_id'] = developerinfo['_id'].__str__()
            self._redis.hmset(developerinfokey, developerinfo_redis)
            

            #更新上次登陆时间
            self.col_developer.update_one({'_id':developerinfo['_id']},{'$set':{'lastlogintime':datetime.datetime.now()}})
            self.collect_developer_oplog(developerid, username, 'login', developerid, username, dict())

            retdict['errcode'] = self.ERRORCODE_OK
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
            retbody['access_token'] = self._redis.hget(developerinfokey,'access_token')
            retbody['developerid'] = developerid
            retbody.update(developerinfo)
            retbody.pop('_id')
            retbody.pop('password')
            for key in ['create_time','update_time','confirm_time','lastlogintime']:
                if key in retbody:
                    retbody[key] = retbody[key].__str__()
            #retbody['create_time'] = retbody['create_time'].__str__()
            return

        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            retdict['errcode'] = self.ERRORCODE_SERVER_ABNORMAL
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_SERVER_ABNORMAL)

        
    def _proc_action_update(self, version, action_body, retdict, retbody):
        '''
        input : {    'action_cmd'  : 'gear_add', M
                     'seq_id      : M
                     'version'    : M
                     'body'   :{
                        'to'    : M
                        'content'     : M
                        'carrier'     : M
                        'notify_type'   : M
                        
                    }
                }

        output:{   
                   'errcode       : "200"'
                   'seq_id'         : M
                }
        '''
        logr.debug(" into _proc_action_update action_body:%s"%action_body)
        try:
#        if 1:
            
            if ('developerid' not in action_body):
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['developerid'] is None:
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            developerid = action_body['developerid']
            inputinfo = dict()
            inputinfo.update(action_body)
            inputinfo.pop('developerid')
            updatedict = self.parse_param_lowlevel(inputinfo)
            developerinfo = self.col_developer.find_one({'_id':ObjectId(developerid)})
            if developerinfo is None:
                retdict['errcode'] = self.ERRORCODE_DEVELOPER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DEVELOPER_NOT_EXIST)
                return

            self.col_developer.update_one({'_id':ObjectId(developerid)},{'$set':updatedict})

            self.collect_developer_oplog(developerid, developerinfo['username'], 'update', developerid, developerinfo['username'], updatedict)


            retdict['errcode'] = self.ERRORCODE_OK
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
            return

        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            retdict['errcode'] = self.ERRORCODE_SERVER_ABNORMAL
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_SERVER_ABNORMAL)

    def _proc_action_auth_url(self, version, action_body, retdict, retbody):
        '''
        input : {    'action_cmd'  : 'gear_add', M
                     'seq_id      : M
                     'version'    : M
                     'body'   :{
                        'to'    : M
                        'content'     : M
                        'carrier'     : M
                        'notify_type'   : M
                        
                    }
                }

        output:{   
                   'errcode       : "200"'
                   'seq_id'         : M
                }
        '''
        logr.debug(" into _proc_action_auth_url action_body:%s"%action_body)
        try:
            if ('developerid' not in action_body) or ('dest_url' not in action_body) or ('token' not in action_body):
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['developerid'] is None or action_body['dest_url'] is None or action_body['token'] is None:
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            developerid = action_body['developerid']
            dest_url = urllib.unquote(action_body['dest_url'].encode('utf-8')).decode('utf-8')
            token = action_body['token']
            developerinfo = self.col_developer.find_one({'_id':ObjectId(developerid)})
            if developerinfo is None:
                retdict['errcode'] = self.ERRORCODE_DEVELOPER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DEVELOPER_NOT_EXIST)
                return
            #如果目标地址为空，就删除所有相关的vid
            if dest_url == '':
                for vid in developerinfo['vidlist']:
                    key = self.KEY_VID % (vid)
                    if self._redis.exists(key):
                        self._redis.delete(key)
            else:
                timestr = '%.0f' % (time.time())
                nonce = str(random.randint(0,1000000))
                logr.debug('token=%s,timestr=%s,nonce=%s',token, timestr, nonce)
                tmpList = [token, timestr, nonce]
                tmpList.sort()
                tmpstr = "%s%s%s" % tuple(tmpList)
                hashstr = hashlib.sha1(tmpstr).hexdigest()
    #            tmpstr = '%s%s%s' % (token,timestr,nonce)
    #            hashstr = hashlib.sha1(tmpstr).hexdigest()
                if dest_url.startswith('http') is False:
                    dest_url='http://%s'%(dest_url)
                httpurl = ('%s?timestamp=%s&nonce=%s&token=%s' % (dest_url, timestr, nonce, token))
                logr.debug('dest_url=%s' % (httpurl))
                http2 = httplib2.Http()
                http2.timeout = 2
                response, content = http2.request(httpurl, method="GET")
                logr.debug("hashstr=%s content = %s" % (hashstr, content))
                if hashstr == content:
                    for vid in developerinfo['vidlist']:
                        key = self.KEY_VID % (vid)
                        self._redis.hmset(key, {'developerid':developerid,'dest_url':dest_url})
                else:
                    retdict['errcode'] = self.ERRORCODE_DESTURL_AUTH_FAILED
                    retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DESTURL_AUTH_FAILED)
                    return


            self.col_developer.update_one({'_id':ObjectId(developerid)},{'$set':{'dest_url':dest_url}})

            self.collect_developer_oplog(developerid, developerinfo['username'], 'auth_url', developerid, developerinfo['username'], {'dest_url':dest_url})


            retdict['errcode'] = self.ERRORCODE_OK
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
            return

        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            retdict['errcode'] = self.ERRORCODE_SERVER_ABNORMAL
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_SERVER_ABNORMAL)

    def _proc_action_update_vid(self, version, action_body, retdict, retbody):
        '''
        input : {    'action_cmd'  : 'gear_add', M
                     'seq_id      : M
                     'version'    : M
                     'body'   :{
                        'to'    : M
                        'content'     : M
                        'carrier'     : M
                        'notify_type'   : M
                        
                    }
                }

        output:{   
                   'errcode       : "200"'
                   'seq_id'         : M
                }
        '''
        logr.debug(" into _proc_action_update_vid action_body:%s"%action_body)
        try:
#        if 1:
            if ('developerid' not in action_body) or ('vidlist' not in action_body) or ('operid' not in action_body) or ('opername' not in action_body) :
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['developerid'] is None or action_body['vidlist'] is None or action_body['operid'] is None or action_body['opername'] is None:
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            developerid = action_body['developerid']
            vidlist = action_body['vidlist']
            opername = urllib.unquote(action_body['opername'].encode('utf-8')).decode('utf-8')
            operid = action_body['operid']
            developerinfo = self.col_developer.find_one({'_id':ObjectId(developerid)})
            if developerinfo is None:
                retdict['errcode'] = self.ERRORCODE_DEVELOPER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DEVELOPER_NOT_EXIST)
                return

            deletevid = list(set(developerinfo.get('vidlist')).difference(set(vidlist)))

            for vid in deletevid:
                key = self.KEY_VID % (vid)
                if self._redis.exists(key):
                    self._redis.delete(key)

            if developerinfo.get('dest_url') is not None and developerinfo.get('dest_url') != '':
                for vid in vidlist:
                    key = self.KEY_VID % (vid)
                    self._redis.hmset(key, {'developerid':developerid,'dest_url':developerinfo.get('dest_url')})

            updatedict = dict()
            updatedict['vidlist'] = vidlist
            updatedict['confirm_time'] = datetime.datetime.now()

            self.col_developer.update_one({'_id':ObjectId(developerid)},{'$set':updatedict})

            self.collect_developer_oplog(developerid, developerinfo['username'], 'update_vid', operid, opername, {'vidlist':vidlist})


            retdict['errcode'] = self.ERRORCODE_OK
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
            return
        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            retdict['errcode'] = self.ERRORCODE_SERVER_ABNORMAL
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_SERVER_ABNORMAL)

    def _proc_action_validate_sdk(self, version, action_body, retdict, retbody):
        '''
        input : {    'action_cmd'  : 'gear_add', M
                     'seq_id      : M
                     'version'    : M
                     'body'   :{
                        'to'    : M
                        'content'     : M
                        'carrier'     : M
                        'notify_type'   : M
                        
                    }
                }

        output:{   
                   'errcode       : "200"'
                   'seq_id'         : M
                }
        '''
        logr.debug(" into _proc_action_validate_sdk action_body:%s"%action_body)
        try:
#        if 1:
            if ('appid' not in action_body) or ('secret' not in action_body) or ('vid' not in action_body):
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['appid'] is None or action_body['secret'] is None or action_body['vid'] is None :
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            appid = action_body['appid']
            secret = action_body['secret']
            vid = action_body['vid']

            bundle_id = action_body.get('bundle_id')
            package_name = action_body.get('package_name')
            # sdk_build = action_body.get('sdk_build')
            # sdk_version = action_body.get('sdk_version')
            # app_version = action_body.get('app_version')
            # app_build = action_body.get('app_build')
            # app_name = action_body.get('app_name')
            retbody['expire'] = self.VALIDATE_SDK_TIMEOUT

            extrainfo = dict()
            extrainfo.update(action_body)
            extrainfo['platform'] = 'UNKNOWN'
            if bundle_id is not None and len(bundle_id)>0:
                extrainfo['platform'] = 'iOS'
            if package_name is not None and len(package_name)>0:
                extrainfo['platform'] = 'Android'


            phone_id = ''
            if 'phone_id' in action_body:
                phone_id = action_body['phone_id']
            phone_name = ''
            if 'phone_name' in action_body:
                phone_name = urllib.unquote(action_body['phone_name'].encode('utf-8')).decode('utf-8')
            # #for test    
            # if appid == 'test':
            #     retdict['errcode'] = self.ERRORCODE_OK
            #     retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
            #     return

            developerinfo = self.col_developer.find_one({'appid': appid, 'secret':secret})
            if developerinfo is None:
                retdict['errcode'] = self.ERRORCODE_DEVELOPER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DEVELOPER_NOT_EXIST)
                return

            self.collect_developer_oplog(developerinfo['_id'].__str__(), developerinfo['username'], 'validate_sdk', phone_id, phone_name, extrainfo)

            if vid not in developerinfo['vidlist']:
                retdict['errcode'] = self.ERRORCODE_VID_ERROR
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_VID_ERROR)
                return
            #检查bundleid/packagename
            developer_id = developerinfo.get('_id').__str__()
            if bundle_id is None and package_name is None:
                #如果是什么信息都没有的话就查看trust记录文件
                fileobj = open("/opt/Keeprapid/OpenApiRonaldo/server/conf/sdk_auth.json", "r")
                sdk_auth = json.load(fileobj)
                fileobj.close()
                trustlist = sdk_auth.get('trust_list')
                if trustlist is not None and vid in trustlist:
                    logr.debug("validate_sdk::[%s] in Trust_List" %(vid))
                    retdict['errcode'] = self.ERRORCODE_OK
                    retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
                    return
                else:
                    logr.error("validate_sdk::[%s] NOT in Trust_List" %(vid))
                    retdict['errcode'] = self.ERRORCODE_VID_ERROR
                    retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_VID_ERROR)
                    return

            if bundle_id is not None and package_name is not None:
                logr.error("validate_sdk::Bundle_ID [%s] and Package_Name[%s] ALL EXISTS" %(bundle_id, package_name))
                retdict['errcode'] = self.ERRORCODE_BUNDLEID_ERROR
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_BUNDLEID_ERROR)
                return

            if bundle_id is not None and len(bundle_id)>0:
                applistinfo = self.col_applist.find_one({"developerid":developer_id,"bundle_id":bundle_id})
                if applistinfo is None:
                    logr.error("validate_sdk::Bundle_ID [%s] NOT EXISTS" %(bundle_id))
                    retdict['errcode'] = self.ERRORCODE_BUNDLEID_ERROR
                    retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_BUNDLEID_ERROR)
                    return
                else:
                    state = applistinfo.get('state')
                    if state is not None and state == 0:
                        logr.error("validate_sdk::Bundle_ID [%s] NOT ACTIVE" %(bundle_id))
                        retdict['errcode'] = self.ERRORCODE_BUNDLEID_ERROR
                        retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_BUNDLEID_ERROR)
                        return

            if  package_name is not None and len(package_name)>0:
                applistinfo = self.col_applist.find_one({"developerid":developer_id,"package_name":package_name})
                if applistinfo is None:
                    logr.error("validate_sdk::Package_Name [%s] NOT EXISTS" %(package_name))
                    retdict['errcode'] = self.ERRORCODE_BUNDLEID_ERROR
                    retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_BUNDLEID_ERROR)
                    return
                else:
                    state = applistinfo.get('state')
                    if state is not None and state == 0:
                        logr.error("validate_sdk::Package_Name [%s] NOT ACTIVE" %(Package_Name))
                        retdict['errcode'] = self.ERRORCODE_BUNDLEID_ERROR
                        retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_BUNDLEID_ERROR)
                        return

            retdict['errcode'] = self.ERRORCODE_OK
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
            return
        except Exception as e:
            logr.error("%s except raised : %s " % (e.__class__, e.args))
            retdict['errcode'] = self.ERRORCODE_SERVER_ABNORMAL
            retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_SERVER_ABNORMAL)

if __name__ == "__main__":
    ''' parm1: moduleid,
    '''
    fileobj = open("/opt/Keeprapid/OpenApiRonaldo/server/conf/config.conf", "r")
    _config = json.load(fileobj)
    fileobj.close()

    thread_count = 1
    if _config is not None and 'developer' in _config and _config['developer'] is not None:
        if 'thread_count' in _config['developer'] and _config['developer']['thread_count'] is not None:
            thread_count = int(_config['developer']['thread_count'])

    for i in xrange(0, thread_count):
        obj = Developer(i)
        obj.setDaemon(True)
        obj.start()

    while 1:
        time.sleep(1)
