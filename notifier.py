import gapy
import json, os, sys
from requests.exceptions import ConnectionError
import time

############################
#check if already running
# import psutil    
# "someProgram" in (p.name() for p in psutil.process_iter())
############################

#necessary both for idle time and admin rights start
from ctypes import windll

###################################################################################
#before anything check if file autoruns at windows start
# import sys --> Already Imported

def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False

skip=False
startup_dir = "C:/Users/"+os.getlogin()+"/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/"
if os.path.exists(startup_dir+"notifier.lnk"):
    skip = True

if not skip:

    import winshell # also needs os but already imported
    from win32com.client import Dispatch

    def makeshortcut():
        startup_dir = "C:/Users/"+os.getlogin()+"/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/"
        path = os.path.join(startup_dir+"notifier.lnk")
        wDir = os.getcwd()+"\\"
        target = wDir + os.path.basename(__file__)
        icon = target
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()

    makeshortcut()

####################################################################

#idle time
from ctypes import Structure, c_uint, sizeof, byref

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def idle_time():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return int(millis / 1000.0)


#browser
import webbrowser
webbrowser.register('firefox', None, webbrowser.BackgroundBrowser("C://Program Files//Mozilla Firefox//firefox.exe"))

#win10toast
from toaster import ToastNotifier
toaster = ToastNotifier()

print("Program Start!")

####################################################################################################

class Gaper():
    def __init__(self, user):
        self.u = user
    def check_toasted(self):
        #get an array of WorkTiles for each thing you have to do
        work = u.fetch_work()

        #check if user idle and wait for return to display the notifications
        while True:
            if idle_time()<5: break
            
        #print properties of each WorkTile
        for i in work:
            if i.id not in idlist:
                self.current = i
                toaster.show_toast(i.title,i.text,icon_path="icon.ico",duration=5,callback_on_click=self.open_gepi)
                idlist.append(i.id)
        with open("idlist.list", "w") as file:
            file.write("\n".join([str(i) for i in idlist]))
    def open_gepi(self):
        print("open gepi here: ", self.current.id)
        webbrowser.get('firefox').open("http://lfabuc.fr/ac/")


idlist = []
if os.path.exists("idlist.list"):
    with open("idlist.list", "r") as file:
        idlist = [int(i) for i in file.read().split("\n") if i !=""]

#get the credentials
cred_path = "credentials.txt"
if os.path.exists(cred_path):
    with open(cred_path, "r") as file:
        usr, psw = file.read().split("\n")[:2]
else:
    with open(cred_path, "w") as file:
        file.write("username\npassword")
    sys.exit()

#create a user here
u = gapy.User.create(usr,psw)

if u:
    u.connect()

    gaper = Gaper(u)

    while True:
        gaper.check_toasted()
        time.sleep(30*60)
    
    u.disconnect()
else:
    print("wrong credentials")
