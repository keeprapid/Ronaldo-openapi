#!/usr/bin/python
# -*- coding: UTF-8 -*-
# filename:  httpgeproxy.py
# creator:   gabriel.liao
# datetime:  2013-6-17

"""http proxy server base gevent server"""
from gevent import monkey
monkey.patch_all()
# monkey.patch_os()
from gevent import socket
from gevent.server import StreamServer
from multiprocessing import Process
import logging
import logging.config
import threading
import uuid
import time
import sys
from Queue import Queue
import redis
import os
import json
import random

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

logging.config.fileConfig("/opt/Keeprapid/OpenApiRonaldo/server/conf/log.conf")
logger = logging.getLogger('ronaldo')

class HttpProxyConsumer(threading.Thread):

    def __init__(self, responsesocketdict):  # 定义构造器
        logger.debug("Created HttpProxyConsumer instance")
        threading.Thread.__init__(self)
        self._response_socket_dict = responsesocketdict
        fileobj = open('/opt/Keeprapid/OpenApiRonaldo/server/conf/db.conf', 'r')
        self._json_dbcfg = json.load(fileobj)
        fileobj.close()

        fileobj = open("/opt/Keeprapid/OpenApiRonaldo/server/conf/config.conf", "r")
        self._config = json.load(fileobj)
        fileobj.close()

        fileobj = open("/opt/Keeprapid/OpenApiRonaldo/server/conf/errmsg.conf", "r")
        self._errmsg = json.load(fileobj)
        fileobj.close()

        self._redis = redis.StrictRedis(self._json_dbcfg['local_redisip'], int(self._json_dbcfg['local_redisport']),password=self._json_dbcfg['local_redispassword'])


    def procdata(self, recvdata):
        recvbuf = json.loads(recvdata)
        if 'sockid' in recvbuf:
#            logger.debug(self._response_socket_dict)
            if recvbuf['sockid'] in self._response_socket_dict:
                respobj = self._response_socket_dict.pop(recvbuf['sockid'])
#                logger.debug(respobj)
                if respobj is not None and 'sock' in respobj:
                    respsockobj = respobj['sock']
#                    logger.debug("Recver callback [%s]" % (recvdata))
                    if 'from' in recvbuf:
                        recvbuf.pop('from')
                    if 'sockid' in recvbuf:
                        recvbuf.pop('sockid')
                    # respsockobj.sendall('HTTP/1.1 200 OK\n\n%s' % (json.dumps(recvbuf)))
                    respsockobj.sendall('HTTP/1.1 200 OK\nContent-Type: application/json\n\n%s' % (json.dumps(recvbuf)))
                    respsockobj.shutdown(socket.SHUT_WR)
                    respsockobj.close()


    def run(self):
        queuename = "A:Queue:httpproxy"
        if self._config is not None and 'httpproxy' in self._config and self._config['httpproxy'] is not None:
            if 'Consumer_Queue_Name' in self._config['httpproxy'] and self._config['httpproxy']['Consumer_Queue_Name'] is not None:
                queuename = self._config['httpproxy']['Consumer_Queue_Name']

        listenkey = "%s:%s" % (queuename, os.getpid())
        logger.debug("HttpProxyConsumer::run listen key = %s" % (listenkey))
        while 1:
            try:
                recvdata = self._redis.brpop(listenkey)
#                logger.debug(recvdata)
                self.procdata(recvdata[1])

            except Exception as e:
                logger.error("PublishThread %s except raised : %s " % (e.__class__, e.args))
                time.sleep(1)


class DogThread(threading.Thread):

    '''监控responsesocketdict超时请求
       参数如下：
       responsesocketdict:等待响应的socket字典，内容为字典['sock', 'requestdatetime']
    '''
    def __init__(self, responsesocketdict):  # 定义构造器
        logger.debug("Created DogThread instance")
        threading.Thread.__init__(self)
        self._response_socket_dict = responsesocketdict
        self._timeoutsecond = 60

    def _isoString2Time(self, s):
        '''
        convert a ISO format time to second
        from:2006-04-12 16:46:40 to:23123123
        把一个时间转化为秒
        '''
        ISOTIMEFORMAT = '%Y.%m.%d.%H.%M.%S'
        return time.strptime(s, ISOTIMEFORMAT)

    def calcPassedSecond(self, s1, s2):
        '''
        convert a ISO format time to second
        from:2006-04-12 16:46:40 to:23123123
        把一个时间转化为秒
        '''
        s1 = self._isoString2Time(s1)
        s2 = self._isoString2Time(s2)
        return time.mktime(s1) - time.mktime(s2)

    def run(self):
        logger.debug("DogThread::run")

        while True:
#            if 1:
            try:
#                now = time.strftime(
#                    '%Y.%m.%d.%H.%M.%S', time.localtime(time.time()))
                now = time.time()


                sortedlist = sorted(self._response_socket_dict.items(), key=lambda _response_socket_dict:_response_socket_dict[1]['requestdatetime'], reverse = 0)
#                sortedlist = sorted(self._response_socket_dict.items(), key=lambda _response_socket_dict:_response_socket_dict[1]['requestdatetime'])
                for each in sortedlist:
                    key = each[0]
                    responseobj = each[1]
                    requestdatetime = responseobj['requestdatetime']
                    passedsecond = now - requestdatetime
                    if passedsecond > self._timeoutsecond:
                        tmpobj = self._response_socket_dict.pop(key)
                        sockobj = tmpobj['sock']
                        sockobj.sendall(
                            'HTTP/1.1 500 OK\n\Timeout %s' % (key))
#                        sockobj = responseobj['sock']
                        logger.debug("DogThread close timeout sock[%s]%r" %(key, sockobj))
                        sockobj.close()
#                        del(self._response_socket_dict[key])
                    else:
                        break
#                sorted(self._response_socket_dict.items(), key=lambda _response_socket_dict:_response_socket_dict[1]['requestdatetime'])
#
#                for key in self._response_socket_dict.keys():
#                    responseobj = self._response_socket_dict[key]
#                    requestdatetime = responseobj['requestdatetime']
#                    passedsecond = self.calcPassedSecond(now, requestdatetime)
#                    if passedsecond > self._timeoutsecond:
#                        del(self._response_socket_dict[key])
#                        sockobj = responseobj['sock']
#                        sockobj.sendall(
#                            'HTTP/1.1 500 OK\n\Timeout %s' % (key))
#                        sockobj.close()
#                    else:
#                        break

                time.sleep(0.1)

            except Exception as e:
                logger.warning("DogThread %s except raised : %s " % (e.__class__, e.args))
                time.sleep(0.1)

class Dog2Thread(threading.Thread):

    '''监控responsesocketdict超时请求
       参数如下：
       responsesocketdict:等待响应的socket字典，内容为字典['sock', 'requestdatetime']
    '''
    def __init__(self, responsesocketdict, consumer):  # 定义构造器
        logger.debug("Created Dog2Thread instance")
        self.consumer = consumer
        self.responsesocketdict = responsesocketdict
        threading.Thread.__init__(self)

    def run(self):
        logger.debug("Dog2Thread::run")
        while 1:
            if self.consumer.is_alive() is False:
                logger.error('publishConsumer is dead, dog run')
                self.consumer = HttpProxyConsumer(self.responsesocketdict)
                self.consumer.setDaemon(True)
                self.consumer.start()
            else:
                pass
            time.sleep(10)




if __name__ == "__main__":

    httpclientsocketqueue = Queue()
    responsesocketdict = dict()

    fileobj = open('/opt/Keeprapid/OpenApiRonaldo/server/conf/db.conf', 'r')
    _json_dbcfg = json.load(fileobj)
    fileobj.close()

    fileobj = open("/opt/Keeprapid/OpenApiRonaldo/server/conf/config.conf", "r")
    _config = json.load(fileobj)
    fileobj.close()

    fileobj = open("/opt/Keeprapid/OpenApiRonaldo/server/conf/errmsg.conf", "r")
    _errmsg = json.load(fileobj)
    fileobj.close()

    _redis = redis.StrictRedis(_json_dbcfg['local_redisip'], int(_json_dbcfg['local_redisport']),password=_json_dbcfg['local_redispassword'])
    recv_buf_len = 2048
    port = 443
    queuename = "A:Queue:httpproxy"
    if _config is not None and 'httpproxy' in _config and _config['httpproxy'] is not None:
        if 'Consumer_Queue_Name' in _config['httpproxy'] and _config['httpproxy']['Consumer_Queue_Name'] is not None:
            queuename = _config['httpproxy']['Consumer_Queue_Name']

    selfqueuename = "%s:%s" % (queuename, os.getpid())
    def recvrawsocket2(sockobj, address):
        try:
#        if 1:
            # logger.error(sockobj)
#            logger.debug(dir(sockobj))
            request_path = ""
            body = []
            p = HttpParser()
            seqid = uuid.uuid1()
            requestdict = dict()
            requestdict['sock'] = sockobj
    #                requestdatetime = time.strftime('%Y.%m.%d.%H.%M.%S', time.localtime(time.time()))
            requestdatetime = time.time()
            requestdict['requestdatetime'] = requestdatetime
            responsesocketdict[seqid.__str__()] = requestdict
            # logger.debug("responsesocketdict len = %d", len(responsesocketdict))

            while True:
                request = sockobj.recv(recv_buf_len)
#                logger.warning("request  : %s" % (request))

                recved = len(request)
#                logger.warning("recved   : %d" % (recved))

                if(recved == 0):
                    logger.warning("socket is closed by peer %r" % (sockobj))
                    sockobj.close()
                    break

                nparsed = p.execute(request, recved)
#                logger.warning("nparsed  : %d" % (nparsed))
                if nparsed != recved:
                    logger.warning("parse error")
                    sockobj.close()
                    break

                if p.is_headers_complete():
                    request_headers = p.get_headers()
    #                        for key in request_headers:
    #                        logger.debug("headers complete %s" % (request_headers.__str__()))

    #                        logger.warning("headers complete")

                if p.is_partial_body():
                    body.append(p.recv_body())
    #                        logger.warning("body  : %s" % (body))

                if p.is_message_complete():
    #                        logger.warning("message complete")
                    break

#            logger.debug(p.get_method())
#            logger.debug(p.get_path())
#            logger.debug(p.get_query_string())

            routekey = ""
            servicepath = ""

            # 如果是/xxx格式认为是route key，如果是/xxx/yyy/zzz格式认为是dest service
            request_path = p.get_path()[1:]
            request_pathlist = request_path.split('/')
            servicename = request_pathlist[0]
            action_name = ''
            servicelist = os.listdir('./apps')
            content = dict()
            if p.get_method() == 'GET':
                if servicename == 'showip':
                    sockobj.sendall("HTTP/1.1 200 OK \n\n%s" % (sockobj))
                    sockobj.shutdown(socket.SHUT_WR)
                    sockobj.close()
                    return
                    
                if len(request_pathlist) != 2:
                    ret = dict()
                    ret['errcode'] = '40004'
                    ret['errmsg'] = _errmsg['40004']
                    sockobj.sendall('HTTP/1.1 500 OK\n\n%s' % (json.dumps(ret)))
                    sockobj.shutdown(socket.SHUT_WR)
                    sockobj.close()
                    return

                action_name = request_pathlist[1]

                querystring = p.get_query_string()
                querylist = querystring.split('&')
                action_body = dict()
                for query in querylist:
                    kvlist = query.split('=')
                    action_body[kvlist[0]] = ''.join(kvlist[1:])
                content['action_cmd'] = action_name
                content['seq_id'] = str(random.randint(10000,1000000))
                content['body'] = action_body
                content['version'] = '1.0'

            else:
                if len(body) > 0:                
                    content = json.loads("".join(body))
#                content = "".join(body)

            # logger.debug("servicename=%s,action_name=%s"%(servicename,action_name))
            # logger.debug("content=%r"%(content))
            if servicename == 'testurl':
                sockobj.sendall('HTTP/1.1 200 OK\n\n%s' % (content['body']['signature']))
                sockobj.shutdown(socket.SHUT_WR)
                sockobj.close()
                return

            if servicename in servicelist:
                routekey = "A:Queue:%s" % servicename
                if servicename in _config:
                    routekey = _config[servicename]['Consumer_Queue_Name']
                content['sockid'] = seqid.__str__()
                content['from'] = selfqueuename
                _redis.lpush(routekey, json.dumps(content))
            else:
                ret = dict()
                ret['errcode'] = '40004'
                ret['errmsg'] = _errmsg['40004']
                sockobj.sendall('HTTP/1.1 404 OK\n\n%s' % (json.dumps(ret)))
                sockobj.shutdown(socket.SHUT_WR)
                sockobj.close()


    #                requestdict = dict()
    #                requestdict['sock'] = sockobj
    #                requestdatetime = time.strftime(
    #                    '%Y.%m.%d.%H.%M.%S', time.localtime(time.time()))
    #                requestdict['requestdatetime'] = requestdatetime
    #                responsesocketdict[seqid.__str__()] = requestdict

            # sockobj.sendall('HTTP/1.1 200 OK\n\nWelcome %s' % (
            #    seqid))
            # sockobj.close()

        except Exception as e:
            logger.error("recvrawsocket2 %s except raised : %s " % (e.__class__, e.args))

    def recvrawsocket(sockobj, address):
        '''
        接收客户http请求，将socket对象压入publish队列，由PublishThread处理
        '''
        logger.error(address)
        logger.error(httpclientsocketqueue.qsize())
        httpclientsocketqueue.put(sockobj)



    dogAgent = DogThread(responsesocketdict)
    dogAgent.setDaemon(True)
    dogAgent.start()

#    publishAgent = PublishThread(
#        httpclientsocketqueue, responsesocketdict, recv_buf_len)
#    publishAgent.setDaemon(True)
#    publishAgent.start()

#    response_count = 1
#    for i in range(0,response_count):
#        publishConsumer = HttpProxyConsumer(responsesocketdict)
#        publishConsumer.setDaemon(True)
#        publishConsumer.start()
    publishConsumer = HttpProxyConsumer(responsesocketdict)
#    publishConsumer.setDaemon(True)
#    publishConsumer.start()
    dog2Agent = Dog2Thread(responsesocketdict,publishConsumer)
    dog2Agent.setDaemon(True)
    dog2Agent.start()


    logger.error('Http gevent proxy serving on %d...' % (port))
    server = StreamServer(('', port), recvrawsocket2, backlog=100000,keyfile='/opt/Keeprapid/OpenApiRonaldo/server/conf/server_symantec.key',certfile='/opt/Keeprapid/OpenApiRonaldo/server/conf/server_symantec.pem')
    server.serve_forever()
