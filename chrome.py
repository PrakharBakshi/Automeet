import time
import pyautogui
import win32gui
import win32process
import win32con
import subprocess 
import os
import signal
from datetime import datetime,date
import notif
import ctypes

add_to_url = "?authuser=1"	#find this parameter in url at meet homepage and set it accordingly
xp=['CS301']	#extra parameters to find in window title to get window_id
ttpath="timetable.txt"	#text file with timetable
daystarttime="07:59"	#defines day start time to not have entire program run before 08:00AM
dayendtime="17:30"	#when do all classes end, to stop program


'''	gets screen resolution, 
	used for default position of mouse to not interfere with image recognition'''
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

#wait times for sleep in check loop
times=[10,20,60,600,900]

#simple exception class
class MeetException(RuntimeError):
	def __init__(self,arg):
		self.desc=arg
	def __repr__():
		print(self.desc)

#callback function for enumwindows, each window id is passed here
def callback(hwnd,hwnds):
	if win32gui.IsWindowVisible (hwnd) and win32gui.IsWindowEnabled (hwnd):
		hwnds=hwnds.append(hwnd)

#generates a list of enabled and visible window ids
def get_all_visible_windows():
	hwnds=[]
	win32gui.EnumWindows (callback, hwnds)
	return hwnds

'''	gets window id of google meet window, 
	if multiple meet windows then checks using meet id
	uses extra parameters if unavailable meet id like course code, stored in  xp'''	
def gethwnd(hwnds,meetid):
	x=[]
	for i in hwnds:
		if win32gui.GetWindowText(i).find("Meet") != -1 and win32gui.GetWindowText(i).find("Google Chrome") != -1:
			x.append(i)
	if len(x)!=1:
		for i in x:
			if win32gui.GetWindowText(i).find(meetid) !=-1:
				return i
		for i in x:
			for j in xp:
				if win32gui.GetWindowText(i).find(j) !=-1:
					return i
	else:
		return x[0]
	return None

'''	opens browser window as a process,
	finds window id of that window
	raises exceptions if browser not started or
	window not found'''
def open_browser_window(c):

	si = subprocess.STARTUPINFO()
	si.wShowWindow=win32con.SW_SHOWMAXIMIZED
	si.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
	urlcur=c.link + add_to_url	#uses particular user with general meet id
	try:
		browser=subprocess.Popen(["C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe","--new-window",urlcur], shell=True,startupinfo=si)
		time.sleep(5)
		hwnds=get_all_visible_windows()
		x=gethwnd(hwnds,c.meetid)
		if x != None:
			bwindow=x
			return [browser,bwindow]	#returns [popen object of browser,window id of meet browser window]
		else:
			raise (MeetException("Unable to find window"))

	except MeetException:
		pass

	except Exception:
		raise(MeetException("Unable to create browser"))

#maximizes the given window, sets it to foreground
def maximize_bwindow(bwindow):
	win32gui.SetActiveWindow(bwindow)
	try:
		win32gui.SetForegroundWindow(bwindow)
	except Exception:
		raise (MeetException("Unable to set foreground window"))
	else:
		win32gui.ShowWindow(bwindow,win32con.SW_MAXIMIZE)
		time.sleep(5)

#boolean function checks if google meet window exists
def checkwindow(meetid):
	time.sleep(2)
	if( gethwnd(get_all_visible_windows(),meetid) == None):
		return False
	else:
		return True

#driver to start class and maximize window to aid pyautogui
def startclass(urlcur,c=0):
	brow_bwin=None
	try:
		brow_bwin=open_browser_window(urlcur)
	except MeetException:
		print(MeetException)
		if (c<=3):
			print("TRYING AGAIN")
			c=c+1
			startclass(urlcur,c)
		else:
			print("TRIES EXCEEDED")
	else:
		try:
			maximize_bwindow(brow_bwin[1])
		except MeetException:
			print(MeetException)
		else:
			time.sleep(3)
			return brow_bwin

#ends class using ctrl+w hotkey on maximized meet window
def endclass(bwindow):
	maximize_bwindow(bwindow)
	time.sleep(5)
	pyautogui.hotkey('ctrl', 'w')
	
#uses image recognition and pyautogui to mute mic, turn cam off, mute site and join class
def joinclass():
	pyautogui.moveTo(user32.GetSystemMetrics(0)/2,0) #moving cursor out of the way due to image recognition
	cc=[]	#click coordinates
	cc.append(pyautogui.locateOnScreen('join2.png'))
	cc.append(pyautogui.locateOnScreen('cam_on2.png'))
	cc.append(pyautogui.locateOnScreen('meetlogo.png'))
	cc.append(pyautogui.locateOnScreen('mic_unmuted.png'))
	if(cc[0]!=None):
		for i in cc:
			if i != None:
				i=pyautogui.center(i)
		pyautogui.hotkey('ctrl', 'e')
		time.sleep(1)
		pyautogui.hotkey('ctrl', 'd')
		if(cc[2]!=None):
			pyautogui.rightClick(cc[2])
			cc.append(pyautogui.locateOnScreen('mutesite.png'))
			if(cc[4] != None):
				cc[4]=pyautogui.center(cc[4])
				pyautogui.click(cc[4])
		'''if(cc[1]!=None):
			pyautogui.click(cc[1])
		if(cc[3]!=None):
			pyautogui.click(cc[3])'''
		pyautogui.click(cc[0])
		pyautogui.moveTo(user32.GetSystemMetrics(0)/2,0)
		time.sleep(2)
		jo=[]
		jo.append(pyautogui.locateOnScreen('recorded.png'))
		if (jo[0]!=None):
			jo.append(pyautogui.locateOnScreen('join_recorded'))
			if (jo[1]!=None):
				jo[1]=pyautogui.center(jo[1])
				pyautogui.click(jo[1])
	else:
		raise MeetException("Unable to find join")

#each object stores day, link, starting and end times of each class
class ClassTime:
	def __init__(self,day,start_time,end_time,link):
		self.day=day
		self.link=link
		self.start_time = datetime.strptime(start_time, "%H:%M")
		self.end_time = datetime.strptime(end_time, "%H:%M")
		self.start_time = self.start_time.time()
		self.end_time = self.end_time.time()
		self.meetid=link[24:]
		if day == "Monday":
			self.dayint=0
		elif day == "Tuesday":
			self.dayint=1
		elif day == "Wednesday":
			self.dayint=2
		elif day == "Thursday":
			self.dayint=3
		elif day == "Friday":
			self.dayint=4

	def __repr__(self):
		return "{} {}-{} {}".format(self.day,self.start_time,self.end_time,self.link)

#gets timetable from text file in ttpath directory
def gettimetable(ttpath):
	file=open(ttpath,"r")
	ttraw=file.readlines()
	tt=[]
	x=["Monday","Tuesday","Wednesday","Thursday","Friday"]
	for i in range(len(ttraw)):
		ttraw[i]=ttraw[i].strip("\n")
	for i in ttraw:
		if i in x:
			day=i
		if i not in x:
			ts=i[1:6]
			te=i[7:12]
			l=i[14:]
			tt.append(ClassTime(day,ts,te,l))
	return tt

#finds class to join, return classtime object if class is  found
def findclasstojoin(tt):
	for i in tt:
		nowd=datetime.now()
		day=nowd.weekday()
		time=nowd.time()
		if day<=4:
			for i in tt:
				if day == i.dayint and time>i.start_time and time<i.end_time:
					return i
		return None

#finds class to join, if true then joins class once, leaves when class time ends

def attendclass(tt):
	curjoin=""
	end = False
	join = False
	brow_bwin=None
	while end == False:
		c=findclasstojoin(tt)
		if c!=None and (curjoin == c.link or curjoin == ""):
			if join == False:
				notif.display_window()
				brow_bwin=startclass(c)
				joinclass()
				join=True
				curjoin=c.link
			else:
				time.sleep(times[3])
		else:
			if join == True:
				count=0
				endc=False
				while count <=2 and endc == False:
					notif.display_window()
					endclass(brow_bwin[1])
					count=count+1
					endc=(not checkwindow(curjoin))
			curjoin=""
			join=False
			if(c==None):
				end=True
	
#loop which sleeps for times seconds and checks for classes to attend till daystarttime < time_now < dayendtime
def initialize():
	nowd=datetime.now()
	timet=nowd.time()
	f=True
	while f==True:
		nowd=datetime.now()
		timet=nowd.time()
		if (timet>ds and timet<dt):
			attendclass(p)
			time.sleep(times[3])
		elif timet<dt :
			time.sleep(times[3])
		else:
			print("CONGRATULATIONS. YOUR DAY HAS ENDED")
			f=False


p=gettimetable(ttpath)
dt=datetime.strptime(dayendtime,"%H:%M")
ds=datetime.strptime(daystarttime,"%H:%M")
dt=dt.time()
ds=ds.time()
initialize()
