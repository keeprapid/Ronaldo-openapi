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


class DataModule(threading.Thread, workers.WorkerBase):

    def __init__(self, moduleid):
        logr.debug("DataModule :running in __init__")
        threading.Thread.__init__(self)
        workers.WorkerBase.__init__(self, moduleid)
#        self.mongoconn = pymongo.Connection(self._json_dbcfg['mongo_ip'],int(self._json_dbcfg['mongo_port']))
        self.mongoconn = pymongo.MongoClient('mongodb://%s:%s@%s:%s/' % (self._json_dbcfg['local_dbuser'],self._json_dbcfg['local_dbpwd'],self._json_dbcfg['local_dbip'],self._json_dbcfg['local_dbport']))
#        self._redis = redis.StrictRedis(self._json_dbcfg['redisip'], int(self._json_dbcfg['redisport']))
        self.db = self.mongoconn.openapi
        self.col_developer = self.db.developer
        
        self.mongoconn1 = pymongo.MongoClient('mongodb://%s:%s@%s:%s/' % (self._json_dbcfg['local_dbuser'],self._json_dbcfg['local_dbpwd'],self._json_dbcfg['local_dbip'],self._json_dbcfg['local_dbport']))
#        self._redis = redis.StrictRedis(self._json_dbcfg['redisip'], int(self._json_dbcfg['redisport']))
        self.db_data = self.mongoconn1.datacenter
        self.col_summary = self.db_data.summary

        self.mongoconn2 = pymongo.MongoClient('mongodb://%s:%s@%s:%s/' % (self._json_dbcfg['master_dbuser'],self._json_dbcfg['master_dbpwd'],self._json_dbcfg['master_dbip'],self._json_dbcfg['master_dbport']))
#        self._redis = redis.StrictRedis(self._json_dbcfg['redisip'], int(self._json_dbcfg['redisport']))
        self.db2 = self.mongoconn2.openapi
        self.col_developer_oplog = self.db2.oplog

        self.mongoconn3 = pymongo.MongoClient('mongodb://%s:%s@%s:%s/' % (self._json_dbcfg['local_dbuser'],self._json_dbcfg['local_dbpwd'],self._json_dbcfg['local_dbip'],self._json_dbcfg['local_dbport']))
#        self._redis = redis.StrictRedis(self._json_dbcfg['redisip'], int(self._json_dbcfg['redisport']))
        self.db_member = self.mongoconn3.member
        self.col_memberinfo = self.db_member.memberinfo


        self.thread_index = moduleid
        self._redis = redis.StrictRedis(self._json_dbcfg['local_redisip'], int(self._json_dbcfg['local_redisport']),password=self._json_dbcfg['local_redispassword'])
        self.recv_queue_name = "W:Queue:Data"
        if 'data' in self._config:
            if 'Consumer_Queue_Name' in _config['data']:
                self.recv_queue_name = _config['data']['Consumer_Queue_Name']


    def __str__(self):
        pass
        '''

        '''

    def _proc_message(self, recvbuf):
        '''消息处理入口函数'''
        logr.debug('_proc_message')
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
            message_resp_dict = dict()
            message_resp_dict['from'] = self.recv_queue_name
            message_resp_dict['seq_id'] = seqid
            message_resp_dict['sockid'] = sockid
            message_resp_dict['errcode'] = '40000'
            message_resp_dict['errmsg'] = self._errmsg.get('40000')

            self._sendMessage(msgfrom, json.dumps(message_resp_dict))
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
        logr.debug('action_version : %s' % (action_version))
        if 'body' in msg_in:
            action_body = msg_in['body']
#            logr.debug('action_body : %s' % (action_body))
        else:
            action_body = None
            logr.debug('no action_body')

        if action_cmd == 'get_membersummary':
            self._proc_action_get_membersummary(action_version, action_body, msg_out_head, msg_out_body)
#        elif action_cmd == 'get_memberinfo':
#            self._proc_action_get_memberinfo(action_version, action_body, msg_out_head, msg_out_body)
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

    def generator_accesstoken(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(60))

    def redisdelete(self, argslist):
        logr.debug('%s' % ('","'.join(argslist)))
        ret = eval('self._redis.delete("%s")'%('","'.join(argslist)))
        logr.debug('delete ret = %d' % (ret))


    def run(self):
        logr.debug("Start NotifyCenter pid=%s, threadindex = %s" % (os.getpid(),self.thread_index))
#        try:
        if 1:
            while 1:
                recvdata = self._redis.brpop(self.recv_queue_name)
                t1 = time.time()
                if recvdata:
                    self._proc_message(recvdata[1])
                logr.debug("_proc_message cost %f" % (time.time()-t1))                    

    def collect_developer_oplog(self, developerid, username, optype, operid, opername, extra):
        insertdevicelog = dict()

        #添加登陆记录
        insertlog = dict({\
            'developerid':developerid,\
            'username':username,\
            'optype':optype,\
            'operid':operid,\
            'opername': opername,\
            'extra': extra,\
            'timestamp': datetime.datetime.now(),\
            'timet':time.time()\
            })
        self.col_developer_oplog.insert_one(insertlog)
        return

    def makeAppId(self):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))

    def makeSecret(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(40))


    def _proc_action_get_membersummary(self, version, action_body, retdict, retbody):
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
        logr.debug(" into _proc_action_get_membersummary action_body:%s"%action_body)
        try:
#        if 1:
            
            if ('access_token' not in action_body) or ('memberid' not in action_body) or ('data_type' not in action_body) or ('datestr' not in action_body):
                retdict['errcode'] = self.ERRORCODE_CMD_HAS_INVALID_PARAM
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return
            if action_body['access_token'] is None or action_body['memberid'] is None or action_body['data_type'] is None or action_body['datestr'] is None :
                retdict['errcode'] = self.ERRORCODE_MEMBER_PASSWORD_INVALID
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_CMD_HAS_INVALID_PARAM)
                return

            access_token = action_body['access_token']
            memberid = action_body['memberid']
            data_type = action_body['data_type']
            datestr = action_body['datestr']


            tokenkey = self.KEY_TOKEN % (access_token)
            if self._redis.exists(tokenkey) is False:
                retdict['errcode'] = self.ERRORCODE_ACCESSTOKEN_INVALID
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_ACCESSTOKEN_INVALID)
                return
            developerid = self._redis.get(tokenkey)
            developerinfo = self.col_developer.find_one({'_id':ObjectId(developerid)})
            if developerinfo is None:                
                retdict['errcode'] = self.ERRORCODE_DEVELOPER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_DEVELOPER_NOT_EXIST)
                return

            memberinfo = self.col_memberinfo.find_one({'_id':ObjectId(memberid)})
            if memberinfo is None:
                retdict['errcode'] = self.ERRORCODE_MEMBER_NOT_EXIST
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_MEMBER_NOT_EXIST)
                return

            developervidlist = developerinfo['vidlist']
            membervidlist = memberinfo['vid']
            commonlist = list(set(developervidlist).intersection(set(membervidlist)))
            if len(commonlist) == 0:
                retdict['errcode'] = self.ERRORCODE_MEMBER_NOT_BELONGS
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_MEMBER_NOT_BELONGS)
                return


            infolist = ['_id','detail','vid','uid','name','nickname']

            summaryinfo = self.col_summary.find_one({'memberid':memberid,'datestr':datestr})
            if summaryinfo is None:
                retbody['sum_step'] = 0
                retbody['sum_distance'] = 0
                retbody['sum_calories'] = 0
                retbody['sum_sleep'] = 0
                retbody['sum_time'] = 0
                retdict['errcode'] = self.ERRORCODE_OK
                retdict['errmsg'] = self._errmsg.get(self.ERRORCODE_OK)
                return

            sourseinfokey = set(summaryinfo.keys())
            commonkey = sourseinfokey.difference(set(infolist))
            infodict = dict()
            for key in commonkey:
                infodict[key] = self.packet_param_lowlevel(summaryinfo[key])


            retbody.update(infodict)

            self.collect_developer_oplog(developerid, developerinfo['username'], 'get_membersummary',developerid, developerinfo['username'], {'access_token':access_token,'memberid':memberid,'datestr':datestr,'data_type':data_type})
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
    if _config is not None and 'data' in _config and _config['data'] is not None:
        if 'thread_count' in _config['data'] and _config['data']['thread_count'] is not None:
            thread_count = int(_config['data']['thread_count'])

    for i in xrange(0, thread_count):
        obj = DataModule(i)
        obj.setDaemon(True)
        obj.start()

    while 1:
        time.sleep(1)
