#!/bin/bash
ps aux|grep /opt/Clousky/Barbarossa/server|awk '{print $2}'|xargs kill -9
