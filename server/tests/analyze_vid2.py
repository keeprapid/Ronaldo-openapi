#!/usr/bin/python
# -*- coding: UTF-8 -*-
# SMGP v3.0 api file
import sys
import pymongo
from bson.objectid import ObjectId
import datetime
import xlrd
import xlwt
import json


if __name__ == "__main__":
    ''' parm1: moduleid,
    '''
    # print macinfodict
    # print macvidinfo
    # print phoneinfo
    # print memberinfo
    fb = open('macinfo.txt','r')
    macinfodict = json.loads(fb.read())
    fb.close()

    fb = open('macvidinfo.txt','r')
    macvidinfo = json.loads(fb.read())
    fb.close()

    fb = open('phoneinfo.txt','r')
    phoneinfo = json.loads(fb.read())
    fb.close()

    fb = open('memberinfo.txt','r')
    memberinfo = json.loads(fb.read())
    fb.close()



    macinfowb = xlwt.Workbook(encoding = 'ascii')
    j = 1
    k = 1
    for key in macinfodict:
        if j == 1:
            macinfosheet = macinfowb.add_sheet('macinfo%d' % (k))
            macinfosheet.write(0,0,'macname')
            macinfosheet.write(0,1,'macvid')
            macinfosheet.write(0,2,'authcount')
            macinfosheet.write(0,3,'macid')
            macinfosheet.write(0,4,'createtime')
            macinfosheet.write(0,5,'authdetail')

        macinfosheet.write(j,0,macinfodict[key]['macname'])
        macinfosheet.write(j,1,macinfodict[key]['macvid'])
        macinfosheet.write(j,2,macinfodict[key]['authcount'])
        macinfosheet.write(j,3,macinfodict[key]['macid'])
        macinfosheet.write(j,4,macinfodict[key]['createtime'])
        macinfosheet.write(j,5,macinfodict[key]['authdetail'])
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

    phonesheet = macinfowb.add_sheet('phoneinfo')
    phonesheet.write(0,0,'phoneid')
    phonesheet.write(0,1,'name')
    phonesheet.write(0,2,'os')
    phonesheet.write(0,3,'nation')
    j = 1
    for key in phoneinfo:
        phonesheet.write(j,0,phoneinfo[key]['phoneid'])
        phonesheet.write(j,1,phoneinfo[key]['phonename'])
        phonesheet.write(j,2,phoneinfo[key]['phoneos'])
        phonesheet.write(j,3,phoneinfo[key]['nation'])
        j+=1

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

    macinfowb.save('macinfo.xls')










