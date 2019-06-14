#!/usr/bin/python
# -*- coding: UTF-8 -*-
# SMGP v3.0 api file
import sys
import pymongo
from bson.objectid import ObjectId
import datetime
import xlrd
import xlwt

if __name__ == "__main__":
    ''' parm1: moduleid,
    '''
    if len(sys.argv) < 2:
        print 'arg2 = VID'
    vid = sys.argv[1]

    conn = pymongo.MongoClient("mongodb://admin:Kr123$^@localhost:27017")
    db = conn.gearcenter
    col_log = db.gear_authlog
    col_mac = db.gear_authinfo

    conn2 = pymongo.MongoClient("mongodb://admin:Kr123$^@localhost:27017")
    db2 = conn2.member
    col_member = db2.memberinfo
    col_devicelog = db2.devicelog

    loglist = col_log.find({'vid':vid})
    macinfodict = dict()
    macvidinfo = dict()
    phoneinfo = dict()
    vidphoneinfo = dict()
    memberinfo = dict()
    i = 0
    total_count = loglist.count()
    for loginfo in loglist:
        macid = loginfo.get('macid')
        phoneid = loginfo.get('phone_id')
        nation = loginfo.get('nation')
        phonename = loginfo.get('phone_name')
        memberid = loginfo.get('memberid')
        phoneos = loginfo.get('phone_os')
        devicename = loginfo.get('device_name')
        macname = "%X" % macid
        if macname not in macinfodict:
            macinfo = col_mac.find_one({'macid':macid})
            createtime = ''
            authtext = list()
            authcount = 0
            macvid = 'notexist'
            if macinfo:
                macvid = macinfo.get('vid')
                ct = macinfo.get('createtime')
                if isinstance(ct, datetime.datetime) :
                    createtime = '%s' % (ct)
                auths = macinfo.get('auths')
                if auths is not None:
                    authcount = len(auths)
                    for authinfo in auths:
                        authtext.append('%s_%s_%s' % (authinfo.get('phone_id'),authinfo.get('phone_name'),authinfo.get('phone_os')))
                        deviceinfo = col_devicelog.find_one({'phone_id':authinfo.get('phone_id'),'vid':vid})
                        if deviceinfo is not None:
                            if deviceinfo['phone_id'] not in vidphoneinfo:
                                a = dict()
                                a['phone_name'] = deviceinfo['phone_name']
                                a['phone_os'] = deviceinfo['phone_os']
                                a['phone_id'] = deviceinfo['phone_id']
                                vidphoneinfo[deviceinfo['phone_id']] = a
            a = dict()
            a['macname'] = macname
            # a['phoneid'] = phoneid
            # a['phonename'] = phonename
            # a['nation'] = nation
            a['macvid'] = macvid
            a['macid'] = macid
            a['authcount'] = authcount
            a['createtime'] = createtime
            a['authdetail'] = '||||'.join(authtext)
            a['device_name'] = devicename
            macinfodict[macname] = a

            if macvid in macvidinfo:
                count = macvidinfo[macvid]
                macvidinfo[macvid] = count+1
            else:
                macvidinfo[macvid] = 1

        if phoneid not in phoneinfo:
            b = dict()
            b['phoneid'] = phoneid
            b['phonename'] = phonename
            b['nation'] = nation
            b['phoneos'] = phoneos
            phoneinfo[phoneid] = b

        if memberid is not None and memberid != '':
            minfo = col_member.find_one({'_id':ObjectId(memberid)})
            if memberid not in memberinfo and minfo is not None:
                c = dict()
                c['username'] = minfo.get('username')
                c['email'] = minfo.get('email')
                source = minfo.get('source')
                sourcetext = 'unknown'
                if source is not None:
                    if isinstance(source,list):
                        sourcetext = ','.join(source)
                    else:
                        sourcetext = source
                c['source'] = sourcetext
                memberinfo[memberid] = c

        i+= 1
        # if i>100:
        #     break

        if i % 1000 == 0:
            print '--------%f(%d/%d)--------done' % (i/(total_count*1.0),i,total_count)
    # print macinfodict
    # print macvidinfo
    # print phoneinfo
    # print memberinfo
    macinfowb = xlwt.Workbook(encoding = 'ascii')
    j = 1
    k = 1
    for key in macinfodict:
        if j == 1:
            macinfosheet = macinfowb.add_sheet('macinfo%d' % (k))
            macinfosheet.write(0,0,'macname')
            macinfosheet.write(0,1,'macvid')
            macinfosheet.write(0,2,'devicename')
            macinfosheet.write(0,3,'authcount')
            macinfosheet.write(0,4,'macid')
            macinfosheet.write(0,5,'createtime')
            macinfosheet.write(0,6,'authdetail')

        macinfosheet.write(j,0,macinfodict[key]['macname'])
        macinfosheet.write(j,1,macinfodict[key]['macvid'])
        macinfosheet.write(j,2,macinfodict[key]['device_name'])
        macinfosheet.write(j,3,macinfodict[key]['authcount'])
        macinfosheet.write(j,4,macinfodict[key]['macid'])
        macinfosheet.write(j,5,macinfodict[key]['createtime'])
        macinfosheet.write(j,6,macinfodict[key]['authdetail'])
        j+=1
        if j>50000:
            j = 1
            k += 1


    macvidsheet = macinfowb.add_sheet('vidinfo')
    macvidsheet.write(0,0,'vid')
    macvidsheet.write(0,1,'count')
    j = 1
    for key in macvidinfo:
        macvidsheet.write(j,0,key)
        macvidsheet.write(j,1,macvidinfo[key])
        j+=1

    k = 1
    j = 1
    for key in phoneinfo:
        if j == 1:          
            phonesheet = macinfowb.add_sheet('phoneinfo_%d'%(k))
            phonesheet.write(0,0,'phoneid')
            phonesheet.write(0,1,'name')
            phonesheet.write(0,2,'os')
            phonesheet.write(0,3,'nation')
        phonesheet.write(j,0,phoneinfo[key]['phoneid'])
        phonesheet.write(j,1,phoneinfo[key]['phonename'])
        phonesheet.write(j,2,phoneinfo[key]['phoneos'])
        phonesheet.write(j,3,phoneinfo[key]['nation'])
        j+=1
        if j>50000:
            j=1
            k+=1

    k = 1
    j = 1
    for key in vidphoneinfo:
        if j == 1:          
            vidphonesheet = macinfowb.add_sheet('vidphone_%d'%(k))
            vidphonesheet.write(0,0,'phoneid')
            vidphonesheet.write(0,1,'name')
            vidphonesheet.write(0,2,'os')
        vidphonesheet.write(j,0,vidphoneinfo[key]['phone_id'])
        vidphonesheet.write(j,1,vidphoneinfo[key]['phone_name'])
        vidphonesheet.write(j,2,vidphoneinfo[key]['phone_os'])
        j+=1
        if j>50000:
            j=1
            k+=1

    if len(memberinfo):
        j=1
        k = 1
        for key in memberinfo:
            if j == 1:
                membersheet = macinfowb.add_sheet('memberinfo_%d'%(k))
                membersheet.write(0,0,'username')
                membersheet.write(0,1,'email')
                membersheet.write(0,2,'source')

            membersheet.write(j,0,memberinfo[key]['username'])
            membersheet.write(j,1,memberinfo[key]['email'])
            membersheet.write(j,2,memberinfo[key]['source'])
            j+=1
            if j>50000:
                j = 1
                k += 1

    macinfowb.save('macinfo_%s.xls'%(vid))










