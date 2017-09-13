import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler
import urllib
import shutil
import io
import time
import cv2
import os
import sys
import subprocess
import numpy as np
from matplotlib import pyplot as plt

BOARDS_FOLDER = "../../resources/boards";
ORIGINAL_FOLDER = "../../resources/original";
globalStartupInfo = subprocess.STARTUPINFO()
globalStartupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
def getFiles(dir):
    return os.listdir(dir)

def getAbspath(path):
    return os.path.abspath(os.path.join(sys.argv[0], path));

def cleanDir(path):
    isExists=os.path.exists(path)
    if isExists:
        shutil.rmtree(path)

def getTemplate():
    constV = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    suits = ['0', '1', '2', '3']
    
    files = []   
    for value in constV:
        for suit in suits:
            name = value+'_'+suit
            template = cv2.imread(os.path.join(BOARDS_FOLDER, name+'.png'),0)
            files.append({
                "name":name,
                "file":template
            })
    return files

def getBoard(img_gray):    
    files = getTemplate()        
    p = []    
    for fileDat in files:
        template = fileDat['file']
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where( res >= threshold)
        isFind = False
        for pt in zip(*loc[::-1]):
            isFind = True
        if isFind:
            p.append(fileDat['name'])
    return p

def getPlayers(dir):
    players = []
    for f in getFiles(ORIGINAL_FOLDER):
        img = cv2.imread(os.path.join(ORIGINAL_FOLDER, f))
        cutImg = img[0:2280,10:300]
        cannyImg = cv2.Canny(cutImg, 200, 300)
        # cv2.imwrite(os.path.join(ORIGINAL_FOLDER, 'a'+f), cannyImg)
        boards = getBoard(cannyImg)
        players.append({
            f:boards
        })
    return players

def runCmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd(), shell=False, startupinfo=globalStartupInfo)
    p.wait()
    re=p.stdout.read().decode()
    return re

def screenshot():
    cleanDir(ORIGINAL_FOLDER)
    os.makedirs(ORIGINAL_FOLDER)
    #adb
    # timestamp = time.strftime('%m%d%H%M%S',time.localtime(time.time())) 
    # os.popen("adb wait-for-device") 
    # tempName = timestamp+".png"  
    # os.popen("adb shell screencap -p /data/local/tmp/"+tempName)  
    # os.popen("adb pull /data/local/tmp/tmp.png " + os.path.join(ORIGINAL_FOLDER, tempName))  
    # os.popen("adb shell rm /data/local/tmp/"+tempName)
    
    curdir=os.getcwd()
    mobiles=[]
    cmd=['adb','devices']
    mobilelist=runCmd(cmd)
    mobilelist=mobilelist.split('\r\n')[1:]
    for x in mobilelist:
        if x:
            mobiles.append(x)
    if not mobiles:
        print(['no devices\t no devices'])
    else:
        for mobiles in mobiles:
            xuliehao=''
            device=mobiles[0].split('\t')
            xuliehao=device[0] 
            if xuliehao:
                timestamp = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
                tempName = xuliehao+"-"+timestamp+".png"  
                jietupath= os.path.join(ORIGINAL_FOLDER, tempName)
                sdcardpath='/sdcard/screenshot-'+tempName
                jtcmd='adb   -s '+xuliehao+' shell /system/bin/screencap -p '+sdcardpath
                # print(jtcmd)
                result=runCmd(jtcmd)
                print('it is screenshot success.....')
                # print(result)
                print('it is moving screenshot to pc.....')
                jtcmd=curdir +'/adb/adb.exe  -s  '+xuliehao+' pull '+sdcardpath+' '+jietupath
                # print(jtcmd)
                result=runCmd(jtcmd)
                # print(result)
                jtcmd=curdir +'/adb/adb.exe   -s '+xuliehao+' shell rm  '+sdcardpath
                # print(jtcmd)
                result=runCmd(jtcmd)
                print(result)
                print('it is moved screenshot to pc success.....')
            else:
                print('no device!')
    

def recognition():
    start = time.clock()
    screenshot()
    hasFile = False
    loopTime = 0
    while (hasFile==False and (loopTime-start)<5):
        if getFiles(ORIGINAL_FOLDER):
            hasFile = True
        else:
            loopTime = time.clock()
    if hasFile==True:
        players = getPlayers(BOARDS_FOLDER)
    else:
        players = []
    end = time.clock()
    print end-start
    return players
        
class MyRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        print self.path
        if 'action' in self.path:
            self.process(2)
        else:
            SimpleHTTPRequestHandler.do_GET(self)
    def responseData(self,data):
        enc="UTF-8"
        content = data.encode(enc)
        f = io.BytesIO()
        f.write(content)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=%s" % enc)
        self.end_headers()
        shutil.copyfileobj(f,self.wfile)
    def process(self,type):
        pw = ''
        timestamp = time.strftime('%d%m%y',time.localtime(time.time())) 
        key = str(hex(int(timestamp)))
        if '?' in self.path:
            query = urllib.splitquery(self.path)
            action = query[0]
            print action
            if query[1]:
                queryParams = {}
                for qp in query[1].split('&'):
                    kv = qp.split('=')
                    if kv[0] == 'pw':
                        pw = kv[1]
        pw = '0x'+pw
        if pw != key:
            self.responseData("")
        else:
            content = recognition()
            self.responseData(str(content))   
                        
if __name__ == "__main__":
    BOARDS_FOLDER = getAbspath(BOARDS_FOLDER)
    ORIGINAL_FOLDER = getAbspath(ORIGINAL_FOLDER)
    ServerClass  = BaseHTTPServer.HTTPServer
    Protocol     = "HTTP/1.0"
    if sys.argv[1:]:
        addr = int(sys.argv[1])
    else:
        addr = ""
    if sys.argv[2:]:
        port = int(sys.argv[2])
    else:
        port = 8000
    server_address = (addr, port)
    
    MyRequestHandler.protocol_version = Protocol
    httpd = ServerClass(server_address, MyRequestHandler)
    
    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()



# # -*- coding:utf-8 -*-
# #https://www.zhaokeli.com/article/8068.html
# import subprocess,os,sys,time
# globalStartupInfo = subprocess.STARTUPINFO()
# globalStartupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
# def runCmd(cmd):
#     p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd(), shell=False, startupinfo=globalStartupInfo)
#     p.wait()
#     re=p.stdout.read().decode()
#     return re
# curdir=os.getcwd()
# mobiles=[]
# cmd=['adb','devices']
# mobilelist=runCmd(cmd)
# mobilelist=mobilelist.split('\r\n')[1:]
# for x in mobilelist:
#     if x:
#         mobiles.append(x)
# if mobiles:
#     print(mobiles)
# else:
#     print(['no devices\t no devices'])
# # xuliehao='';
# # if mobiles:
# #     device=mobiles[0].split('\t')
# #     xuliehao=device[0]
# #     print(device)
# # if xuliehao:
# #     timestamp = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
# #     jietupath='d:/screenshot-'+timestamp+'.png'
# #     sdcardpath='/sdcard/screenshot-'+timestamp+'.png'
# #     if os.path.exists(jietupath):
# #         os.remove(jietupath)
# #     print('it is screenshoting to mobile.....')
# #     jtcmd=curdir +'/adb/adb.exe   -s '+xuliehao+' shell /system/bin/screencap -p '+sdcardpath
# #     # print(jtcmd)
# #     result=runCmd(jtcmd)
# #     print('it is screenshot success.....')
# #     # print(result)
# #     print('it is moving screenshot to pc.....')
# #     jtcmd=curdir +'/adb/adb.exe  -s  '+xuliehao+' pull '+sdcardpath+' '+jietupath
# #     # print(jtcmd)
# #     result=runCmd(jtcmd)
# #     # print(result)
# #     jtcmd=curdir +'/adb/adb.exe   -s '+xuliehao+' shell rm  '+sdcardpath
# #     # print(jtcmd)
# #     result=runCmd(jtcmd)
# #     print(result)
# #     print('it is moved screenshot to pc success.....')
# # else:
# #     print('no device!')

# import cv2
# import numpy as np

# constV = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
# suits = ['0', '1', '2', '3']
# for value in constV:
#     for suit in suits:
#         name = value+'_'+suit
#         img = cv2.imread(name+".png")
#         cv2.imwrite("new/"+name+".png", cv2.Canny(img, 200, 300))