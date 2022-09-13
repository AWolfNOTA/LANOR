import os
import sys
import datetime
import time
from simple_pid  import PID
import tkinter as tk
from tkinter import font as tkFont
from tkinter import ttk
#from ttkthemes import ThemedTk
import piplates.DAQC2plate as DAQC2
import piplates.MOTORplate as MOTOR
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import webbrowser

#DEFINE COLORS + FONTS
RED = "#d63031"
GREEN = "#00b894"
BLUE = "#0984e3"
YELLOW = "#ffeaa7"
PURPLE= "#a29bfe"
FONT= ("Verdana", 10)
#create a global variable for LED values
global percent
percent=0.0

#Utility Functions
#Initialize IO Address
addr = 0
def initADDR3():
    global addr
    addrSet=False
    addresses = [False,False,False,False,False,False,False,False]
    for i in range(8):
        tempADDR=DAQC2.getADDR(i)
        if(tempADDR==i):
            addresses[i]=True
            if(addrSet==False):
                addr=i
                addrSet=True
'''
#Sets DAQC2 PWM Plate Output- needed for PWM output Scale Bars
def setPWM(par1, par2):
    global addr
    par1=float(par1)
    DAQC2.setPWM(addr,par2, par1)
'''
def LED(val):
    #print(val)
    if val != 0:
        #MOTOR.dcCONFIG(1,4,'cw',val,1)
        MOTOR.dcSPEED(1, 4, val)
        MOTOR.dcSTART(1,4)
        MOTOR.dcSPEED(1, 3, val)
        MOTOR.dcSTART(1,3)
    else:
        MOTOR.dcSTOP(1, 4)
        MOTOR.dcSTOP(1,3)
# NoGen custom code to calc gas values and return a string
def nogenNoCalc(anval, bno, span, cno):
    fval=anval
    mno = (span-bno)/cno
    if mno == 0:
        cal.error.set("ERROR")
        return 0
    no_ppm=(fval-bno)/mno
    return no_ppm
            
#UI for stepper motor manual control
class StepperMotor:
    def __init__(self,master):
        self.stepState=0       #stopped
        smColor=RED
        slwidth=30
        slength=120
        self.mVal='A'
        self.master=master
        self.sm=tk.Frame(self.master,padx=4,pady=4,bd=2,relief='flat')
        self.sm.grid(row=2,column=0, rowspan=3, sticky="nsew", columnspan=2)
        self.addr = 1
        
        ##Title
        self.labelt = tk.Label(self.sm, text="Stepper Motor", padx=4,pady=4, bg=smColor,font=FONT, fg="white")
        self.labelt.grid(row=0,column=0,columnspan=6,sticky="we")
        
        ##Step Rate Control
        self.labels = tk.Label(self.sm, text="Step Rate",padx=4,pady=4,font=FONT)
        self.labels.grid(row=1,column=0)
        self.rate=tk.IntVar()
        self.rate.set(0)
        self.RateSet=tk.Scale(self.sm,variable=self.rate,from_=2000,to=0,width=slwidth,length=slength)
        self.RateSet.bind("<ButtonRelease-1>", self.ratedelta)
        self.RateSet.grid(row=2,column=0,rowspan=4)
        self.E_rate = tk.Entry(self.sm, width=8, textvariable=self.rate, font=FONT)
        self.E_rate.grid(row=5, column=1, pady=20, sticky="w")
        self.E_rate.bind("<1>", handle_open)
 
        ##Direction Control
        self.labeld = tk.Label(self.sm, text="Direction",padx=4,pady=4,font=FONT)
        self.labeld.grid(row=1,column=1,sticky="w")       
        self.direction = tk.IntVar()
        self.direction.set(0)
        self.cwb = tk.Radiobutton(self.sm, text='Clockwise', variable=self.direction, value=0)
        self.ccwb = tk.Radiobutton(self.sm, text=' Counter Clockwise', variable=self.direction, value=1)
        self.direction.set(0)
        self.cwb.grid(row=2,column=1,sticky="w")
        self.ccwb.grid(row=3,column=1,sticky="w")
 
        ##Acceleration Control
        self.labela = tk.Label(self.sm, text="Acceleration",padx=4,pady=4,font=FONT)
        self.labela.grid(row=1,column=2)
        self.acc= tk.DoubleVar()
        self.acc.set(0.0)
        self.accSet= tk.Scale(self.sm,variable=self.acc,from_=5.0,to=0.0, resolution=0.1,width=slwidth,length=slength)
        self.accSet.grid(row=2,column=2,rowspan=4)
 
        ##Step Size Control
        rStart = 1     
        self.labeld = tk.Label(self.sm, text="Step Size",padx=4,pady=4,font=FONT)
        self.labeld.grid(row=rStart,column=3,sticky="w") 
        rStart+=1
        self.ss = tk.IntVar()
        self.ss.set(2)  # initializing the choice: Full
        sizes = [
            ("Full",0),
            ("Half",1),
            ("1/4",2),
            ("1/8",3)
            ] 
        
        for txt, val in sizes:
            tk.Radiobutton(self.sm, 
                text=txt, 
                variable=self.ss, 
                value=val).grid(row=rStart+val,column=3,sticky="w")
 
        ##Step Count Control
        self.labelstep = tk.Label(self.sm, text="Step Count",padx=4,pady=4,font=FONT)
        self.labelstep.grid(row=1,column=4)
        self.steps= tk.IntVar()
        self.steps.set(0)
        self.StepSet= tk.Scale(self.sm,variable=self.steps,from_=2000,to=0,width=slwidth,length=slength)
        self.StepSet.grid(row=2,column=4,rowspan=4)                
 
        ##Jog Button
        self.startButton= tk.Button(self.sm,text="JOG", bg=GREEN, fg="white", width=6,command=self.jog, relief='flat')
        self.startButton.grid(row=2,column=5)
 
        ##Move Button
        self.startButton= tk.Button(self.sm,text="MOVE",fg="white",bg=BLUE,width=6,command=self.move, relief='flat')
        self.startButton.grid(row=3,column=5) 
        
        ##Stop Button
        self.stopButton= tk.Button(self.sm,text="STOP",fg="white",bg=RED,width=6,command=self.stop, relief='flat')
        self.stopButton.grid(row=4,column=5)  
 
        ##Off Button
        self.stopButton= tk.Button(self.sm,text="OFF", bg=PURPLE, fg="white", width=6,command=self.off, relief='flat')
        self.stopButton.grid(row=5,column=5) 
        
        self.stop()   #ensure motor is off at start
        self.off()   #ensure motor is off at start
   
    #Sets Rate when changed by User
    def ratedelta(self,val):
        if (self.stepState==1):
            MOTOR.stepperRATE(self.addr,self.mVal,self.rate.get())
 
    #JOG: Motor Continuously Moves
    def jog(self):
        self.stop()
        self.stepState=1
        if (self.direction.get() == 0):
            dir='cw'
        else:
            dir='ccw'
        MOTOR.stepperCONFIG(self.addr,self.mVal,dir,self.ss.get(),self.rate.get(),self.acc.get())
        MOTOR.stepperJOG(self.addr,self.mVal)
    
    #MOVE: Motor moves a given number of steps then stops
    def move(self):
        self.stop()
        self.stepState=2
        if (self.direction.get() == 0):
            dir='cw'
        else:
            dir='ccw'
        MOTOR.stepperCONFIG(self.addr,self.mVal,dir,self.ss.get(),self.rate.get(),self.acc.get())
        MOTOR.stepperMOVE(self.addr,self.mVal,self.steps.get())
    
    #Stops motor Movement
    def stop(self):
        MOTOR.stepperSTOP(self.addr,self.mVal)    
        self.stepState=0            
 
    #Cuts signal to motor
    def off(self):
        MOTOR.stepperOFF(self.addr,self.mVal)    
        self.stepState=0 

#Graphs NO/NO2 Output
class Graph:
    def __init__(self, master):
        self.graph_sp = tk.IntVar()
        self.graph_sp.set(0)
        self.gs = 0
        self.xs = []
        self.ys = []
        self.ys2 = []
        self.setpoints=[]
        self.start_time = time.time()
        tk.Button(master,text="Start Graph",command=self.startgraph,padx=4,pady=4, bg=GREEN, fg="WHITE", width = 12, relief="flat").grid(row=0, column=4, pady=4)
        tk.Button(master,text="Stop Graph",command=self.stopgraph,padx=4,pady=4, bg=RED, fg="WHITE", width = 12, relief="flat").grid(row=1, column=4)
        tk.Checkbutton(master,text="Graph Setpoint", indicatoron=1,bd=0, highlightthickness=0
            ,fg="black", variable=self.graph_sp, selectcolor="white").grid(row=2,column=4, pady=10, padx=16)
        
    def startgraph(self):
        self.start_time = time.time()
        self.xs.clear()
        self.ys.clear()
        self.setpoints.clear()
        self.ys2.clear()
        self.fig, (self.ax, self.ax2) = plt.subplots(2, sharex=True, figsize=(8,8))
        self.gs=1
        ani = animation.FuncAnimation(self.fig, self.animate, fargs=(self.xs, self.ys, self.ys2, self.setpoints), interval=1000)
        plt.show()
    
    def stopgraph(self):
        self.gs=0
        
    def graph(self, no_ppm, no2_ppm, setpoint):
        if self.gs == 1:
            self.setpoints.append(setpoint)
            self.xs.append((time.time()-self.start_time)/60)
            self.ys.append(no_ppm)
            self.ys2.append(no2_ppm)
            if len(self.xs)>= 1200:
                del self.xs[0]
                del self.ys[0]
                del self.ys2[0]
    
    def animate(self, i, xs, ys, ys2, setpoints):
        if self.gs == 1:
            self.ax.clear()
            self.ax2.clear()
            self.ax.plot(xs, ys, linewidth=1, label="NO")
            if self.graph_sp.get()==1:
                self.ax.plot(xs, setpoints, linewidth=1, label="DAC (V)")
            self.ax2.plot(xs, ys2, linewidth=1, label="NO2")
            plt.xticks(rotation=45, ha='right')
            self.ax.set_ylabel("NO (ppm)")
            self.ax2.set_ylabel("NO2 (ppm)")
            plt.subplots_adjust(bottom=0.30)
            plt.xlabel('Time (min)')

#Log NO/NO2 Data
class Log:
    def __init__(self, master, controller):
        self.ls = tk.IntVar()
        self.ls.set(0)
        self.pl = tk.IntVar()
        self.pl.set(0)
        self.log_file = "Log_" + str(datetime.date.today())
        self.log_path = "/home/pi/Desktop/Log_Data"
        self.log_time=1
        self.start = time.time()
        tk.Label(master, text="File Name:",fg="Black").grid(row=0, column=3, sticky="w")
        self.E_file = tk.Entry(master, width=10)
        self.E_file.insert(0,self.log_file)
        self.E_file.grid(row=0, column=3, sticky="e",  padx=(80, 20))
        tk.Label(master, text="Log Rate (s):",fg="Black").grid(row=1, column=3, sticky="w")
        self.E_time = tk.Entry(master, width=10)
        self.E_time.insert(0,str(self.log_time) + " sec")
        self.E_time.grid(row=1, column=3, pady=4, padx=(110, 20), sticky="e")
        tk.Checkbutton(master,text="Logging On",command=self.startlog, variable=self.ls).grid(row=2, column=3, sticky="w")
        tk.Checkbutton(master,text="Log PID Data", indicatoron=1,bd=0, highlightthickness=0
            ,fg="black", variable=self.pl, selectcolor="white"
            ,command=controller.log_pid).grid(row=2,column=3, pady=10, sticky="e")
        
    def startlog(self):
        if self.pl.get() == 1:
            data = "Time (s), NO (ppm), NO2 (ppm), DAC (V), P, I, D\n"
        else:
            data = "Time (s), NO (ppm), NO2 (ppm)\n"
        if self.ls.get() == 1:
            print("starting")
            self.log_file=self.E_file.get()
            self.log_time = float(self.E_time.get().split()[0])
            os.makedirs(self.log_path, exist_ok=True)
            logfile = os.path.join(self.log_path, self.E_file.get() + ".csv")
            if not os.path.isfile(logfile):
                self.start = time.time()
                with open(logfile,'a+') as f:
                    f.write(data)

    def log_data(self, data_in):
        if self.pl.get() == 0:
            data = [data_in[0], data_in[1]]
        else:
            data = data_in
        if self.ls.get()==1 and (int((time.time()-self.start) % self.log_time)==0):
            dt_now = str(int(time.time()-self.start))
            logfile = os.path.join(self.log_path,self.log_file + ".csv")
            data.insert(0, dt_now)
            dt_log=','.join(map(str, data))
            with open(logfile,'a+') as f:
                f.write(dt_log+"\n")
    
#UI with separated windows
class LANOR(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        #Initialize Frames
        top_container = tk.Frame(self, relief='flat')
        top_container.grid(row=0, column=0, rowspan=4, sticky='nsew')
            
        body_container = tk.Frame(self, relief='flat')
        body_container.grid(row=5, column=0)
            
        self.frames = {}
        for F in (ManualPage, AutoPage, CalibratePage):
            frame = F(body_container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(ManualPage)
        self.mode = 0
            
        #References to CalibratePage and AutoPage to access class in Task function
        self.cal = self.frames[CalibratePage]
        self.Pid = self.frames[AutoPage]
            
        #Initialize Analog Inputs
        self.analogin = list(range(4))
        """
        for i in range(0,2):
            tk.Label(top_container,text="Channel "+str(i)+":",padx=4).grid(row=i+1,column=0,sticky="e")    
            self.analogin[i]=tk.StringVar()
            self.analogin[i].set("-----")
            #tk.Label(top_container,textvariable=self.analogin[i],pady=2).grid(row=i+1,column=1, sticky="w")
        """
        
        #add to main loop
        tk.Label(top_container,text="Channel 0:",padx=4).grid(row=1,column=0,sticky="e") 
        self.NO_Voltage= tk.Label(top_container, text = "-----")
        self.NO_Voltage.grid(row=1, column=1, pady=2, sticky="w")
        tk.Label(top_container,text="Channel 1:",padx=4).grid(row=2,column=0,sticky="e") 
        self.NO2_Voltage= tk.Label(top_container, text = "-----")
        self.NO2_Voltage.grid(row=2, column=1, pady=2, sticky="w")
        
        #NO and NO2 Readings
        
        self.NO2_ppm= tk.Label(top_container,text="NO2: -----",padx=4,pady=2)
        self.NO2_ppm.grid(row=2,column=2, sticky="e")
        self.NO_ppm= tk.Label(top_container,text="NO -----",padx=4,pady=2)
        self.NO_ppm.grid(row=1,column=2, sticky="e")
        
        
        
        #Digital Output - Pump
        DAQC2.clrDOUTbit(addr,0)
        self.chkovar= tk.IntVar()
        self.chkovar.set(0)
        #config motor output to control lights
        MOTOR.dcCONFIG(1,3,'cw',0.0,1)
        MOTOR.dcCONFIG(1,4, 'cw', 0.0,0)
        tk.Checkbutton(top_container,text="Pump On", bg=YELLOW, variable=self.chkovar, command=lambda: self.toggleChk(0), padx=20, pady=4).grid(row=0,column=0, columnspan=3)
            
        #Navigation Buttons
        navFrame = tk.Frame(top_container, relief='flat')
        navFrame.grid(row=3, column=0, columnspan=5, sticky='nsew')
        button1 = tk.Button(navFrame, text="Manual Control", command=lambda: self.show_frame(ManualPage), font=FONT, relief='flat',  fg="white", bg=BLUE)
        button1.grid(row=3,column=0, padx=(20,100))
        button2 = tk.Button(navFrame, text="Auto Control", command=lambda: self.show_frame(AutoPage), font=FONT, relief='flat', fg="white", bg=BLUE)
        button2.grid(row=3,column=1)
        button3 = tk.Button(navFrame, text="Calibrate",command=lambda: self.show_frame(CalibratePage), font=FONT, relief='flat',  fg="white", bg=BLUE)
        button3.grid(row=3, column=2, padx=(120,20)) 
            
        #Graphing and logging
        self.graph=Graph(top_container)
        self.log=Log(top_container, self)

        self.after(5000, self.task)
    
    #Toggle which window is shown
    def show_frame(self, cont):
        #0 is manual mode, 1 is auto mode.
        #This Controls whether manual user input controls motor/light or PID function does
        if cont == ManualPage:
            self.mode = 0
        if cont == AutoPage:
            self.mode = 1
        frame = self.frames[cont]
        frame.tkraise()
    
    #Log PID Values when selected
    def log_pid(self):
        if self.log.pl.get() == 1:
            os.makedirs(self.log.log_path, exist_ok = True)
            print("logging")
            logfile = os.path.join(self.log.log_path, self.log.E_file.get() + ".csv")
            data = "KP = "+ str(self.Pid.kp) + ",KI = " + str(self.Pid.ki) + ",KD = " +str(self.Pid.kd) + ",Setpoint = " + str(self.Pid.sp) + ",Sample Time = " + str(self.Pid.sample_time) + "\n"
            with open (logfile, "a+") as f:
                f.write(data)
                f.write("Time (s), NO (ppm), NO2 (ppm), DAC (V), P, I, D\n")
    
    #Needed for pump control
    def toggleChk(self,par):
        global addr
        if self.chkovar.get()==1:
            #print(1)
            DAQC2.setDOUTbit(addr, par)
        else:
            #print(0)
            DAQC2.clrDOUTbit(addr,par)

    
    #Responsible for updating NO/NO2 values, logging, graphing, and updating PID
    def task(self):
        global addr
        global percent
        LED(percent)
        # get Gas (NO NO2) value
        for i in range(0,2): 
            val=DAQC2.getADC(addr,i)
            sval=str('{: 7.3f}'.format(val))
            #self.analogin[i].set(sval)
            if i==0:
                no_ppm = nogenNoCalc(val, self.cal.bno, self.cal.span, self.cal.cno)
                #self.sno_ppm.set("NO: "+str('{: 3.2f}'.format(no_ppm)))
                self.NO_Voltage.config(text= str('{: 7.3f}'.format(DAQC2.getADC(addr,0))))
                self.NO_ppm.config(text=("NO: "+str('{: 3.2f}'.format(no_ppm)))) 
                pid_out = str('{:3.2f}'.format((self.Pid.get_PID(no_ppm))))
                READINGS.NO_FRAME.NO_label.config(text=str(round(no_ppm,0)))
            if i==1:
                no2_ppm=nogenNoCalc(DAQC2.getADC(addr,i), self.cal.bno2, self.cal.span2, self.cal.cno2)
                self.NO2_Voltage.config(text= str('{: 7.3f}'.format(DAQC2.getADC(addr,1))))
                self.NO2_ppm.config(text=("NO2: "+str('{: 3.2f}'.format(no2_ppm))))
                if no2_ppm <= 0:
                    READINGS.NO2_FRAME.NO2_label.config(text="0.0")
                else:
                    READINGS.NO2_FRAME.NO2_label.config(text=str(round(no2_ppm,1)))
                
        #this is the data we want to log, in an array. If the mode is 1 (auto) will log PID info, else will log PWM value
        if self.mode == 1:
            self.log.log_data([no_ppm, no2_ppm, pid_out, self.Pid.pid.components[0], self.Pid.pid.components[1], self.Pid.pid.components[2]])
        else:
            self.log.log_data([no_ppm, no2_ppm, DAQC2.getPWM(addr,0)])
        
        #Graph no, no2, and pass setpoint which will be graphed when it is selected
        self.graph.graph(no_ppm, no2_ppm, self.Pid.sp)
        
        # This next line will add the task function to the processing queue for every 1 sec update      
        self.after(1000, self.task)
class Readings(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.MedFont = ("Helvetica", 30)
        self.LargeFont = ("Helvetica",60)
        self.NO_FRAME = NOFrame(self, bg="white", highlightbackground="black", highlightthickness=1)
        self.NO_FRAME.grid(row=0, column=0, columnspan=2, padx=175)
        self.NO2_FRAME = NO2Frame(self, bg="white", highlightbackground = "black", highlightthickness=1)
        self.NO2_FRAME.grid(row=1, column=0, columnspan=2, padx=175)
    
class NOFrame(Readings):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        tk.Label(self, text="NO", bg="white", font=parent.MedFont).pack()
        self.NO_label = tk.Label(self, text="0", bg="white", font=parent.LargeFont)
        self.NO_label.pack(padx=30, pady=30)

class NO2Frame(Readings):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        tk.Label(self, text="NO\u2082", bg="white", font=parent.MedFont).pack()
        self.NO2_label = tk.Label(self, text="0", bg="white", font=parent.LargeFont)
        self.NO2_label.pack(padx=30, pady=30)
#Window with manual PWM and motor control
class ManualPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        anf = tk.Frame(self)
        anf.grid(row=6, column=0, pady=8, columnspan=2)
        Stepper = StepperMotor(self)
        
        #Analog Outputs
        """
        tk.Label(anf,text="PWM Outputs (Light)",bg=RED, fg="white", padx=4,pady=4).grid(row=0, column=0,columnspan=7, pady=4, padx=4, sticky="ew")
        for i in range(2):
            tk.Label(anf,text='Chan '+str(i),bg=YELLOW, pady=15).grid(row=1+i,column=0, sticky="w", padx=(30, 5))
            slider = tk.Scale(anf,orient=tk.HORIZONTAL,from_=0.0,to=100,resolution=0.001,length=400, width=20,bg=YELLOW)
            slider.grid(row=1+i,column=2, sticky="w", padx=(0,22), columnspan=6)
            tk.Button(anf, text="Set", command = LED(slider.get()), bg=YELLOW, pady=15).grid(row=1+i, column=1, sticky="w", padx=(5, 5))
        """
#Use PID to control light - motor needs to be implemented
class AutoPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # PID Code starts here
        self.file = "/home/pi/Downloads/pid_values.txt"
        self.pid_text= tk.StringVar()
        self.volt_out = tk.DoubleVar()
        self.volt_out.set("---")
        self.pid_text.set("---")
        
        with open(self.file, 'r') as f:
            data = f.readline().split('|')
            self.kp = float(data[0])
            self.ki = float(data[1])
            self.kd = float(data[2])
            self.sp = float(data[3])
            self.sample_time = float(data[4])
            self.min = float(data[5])
            self.max = float(data[6])            
        
        pad_y = 15
        pad_x = 30
        tk.Label(self,text="PID Inputs", bg=YELLOW, pady=4).grid(row=0,column=0, columnspan=5, sticky='nsew', padx=pad_x, pady=4)
        tk.Label(self,text="Kp:",fg="black").grid(row=1,column=1, padx=pad_x, pady=pad_y)
        tk.Label(self,text="Ki:",fg="black").grid(row=2,column=1, padx=pad_x, pady=pad_y)
        tk.Label(self,text="Kd:",fg="black").grid(row=3,column=1, padx=pad_x, pady=pad_y)
        tk.Label(self,text="Setpoint:",fg="black").grid(row=4,column=1, padx=pad_x, pady=pad_y)
        tk.Label(self,text="Sample Time (s):",fg="black").grid(row=3,column=3, padx=pad_x, pady=pad_y)
        tk.Label(self,text="Min Output (V):",fg="black").grid(row=1,column=3, padx=pad_x, pady=pad_y)
        tk.Label(self,text="Max Output (V):",fg="black").grid(row=2,column=3, padx=pad_x, pady=pad_y)
        self.kp_entry= tk.Entry(self, width=8)
        self.kp_entry.grid(row=1, column=2, padx=pad_x, pady=pad_y)
        self.kp_entry.insert(0,self.kp)
        self.ki_entry= tk.Entry(self, width=8)
        self.ki_entry.grid(row=2, column=2, padx=pad_x, pady=pad_y)
        self.ki_entry.insert(0,self.ki)
        self.kd_entry= tk.Entry(self, width=8)
        self.kd_entry.grid(row=3, column=2, padx=pad_x, pady=pad_y)
        self.kd_entry.insert(0,self.kd)
        self.setpoint_entry= tk.Entry(self, width=8)
        self.setpoint_entry.grid(row=4, column=2, padx=pad_x, pady=pad_y)
        self.setpoint_entry.insert(0,self.sp)
        self.time_entry= tk.Entry(self, width=8)
        self.time_entry.grid(row=3, column=4, padx=pad_x, pady=pad_y)
        self.time_entry.insert(0,self.sample_time)
        self.min_entry= tk.Entry(self, width=8)
        self.min_entry.grid(row=1, column=4, padx=pad_x, pady=pad_y)
        self.min_entry.insert(0,self.min)
        self.max_entry= tk.Entry(self, width=8)
        self.max_entry.grid(row=2, column=4, padx=pad_x, pady=pad_y)
        self.max_entry.insert(0,self.max)
        tk.Button(self, text='Submit', fg="white", bg=BLUE, command=self.update_PID, relief='flat').grid(row=5, column=2)
        tk.Button(self, text="Reset", fg="white", bg=BLUE, command=self.reset_PID, relief='flat').grid(row=5, column=1)
        tk.Label(self,text="Output:",fg="black", bg=YELLOW, padx=5).grid(row=5,column=3, sticky="e")
        #make sure to add these to the main loop
        self.out_l = tk.Label(self,text="??? V ",fg="black", bg=YELLOW, padx=8)       
        self.out_l.grid(row=5,column=4, sticky="w")
        self.pid_l = tk.Label(self,text="pid")
        self.pid_l.grid(row=4,column=3, padx=8, columnspan=2, sticky="ew")
        self.pid=PID(Kp=self.kp, Ki=self.ki, Kd=self.kd, setpoint=self.sp,
                     sample_time=self.sample_time, output_limits=(self.min, self.max),
                     auto_mode=True, proportional_on_measurement=False)
                   
    def update_PID(self):
        self.kp = float(self.kp_entry.get())
        self.ki = float(self.ki_entry.get())
        self.kd = float(self.kd_entry.get())
        self.sp  = float(self.setpoint_entry.get())
        self.min = float(self.min_entry.get())
        self.max = float(self.max_entry.get())
        self.sample_time = float(self.time_entry.get())
        self.pid.tunings = (self.kp, self.ki, self.kd)
        self.pid.setpoint = self.sp
        self.pid.sample_time = self.sample_time
        self.pid.output_limits=(self.min,self.max)
        
    def reset_PID(self):
       self.pid=PID(Kp=self.kp, Ki=self.ki, Kd=self.kd, setpoint=self.sp,
                sample_time=self.sample_time, output_limits=(self.min, self.max),
                auto_mode=True, proportional_on_measurement=False)

    def get_PID(self, no_ppm):
        global percent
        if self.controller.mode == 1:
            if self.pid.auto_mode == False: self.pid.auto_mode = True
            light_val=self.pid(no_ppm)
            #print(light_val) 
            self.volt_out.set("{:.3f}".format(float(light_val)))
            self.out_l.config(text =str("{:.3f}".format(float(light_val))))
            components=self.pid.components
            components_strings = []
            for c in components:
                components_strings.append(np.around(float(c), 4))
            components_string=(','.join(map(str, components_strings)))
            self.pid_text.set(components_string)
            self.pid_l.config(text=components_string)
            percent = light_val / 5 *100
            #print(percent)
            LED(percent)
            return light_val
        else:
            self.pid.auto_mode = False
            return 0

#Sensor Calibration
class CalibratePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.bno = 0.0
        self.bno2 = 0.0
        self.span = 0.0
        self.span2 = 0.0
        self.cno = 101
        self.cno2 = 16.1
        self.openfile="/data/lanor/factory_values.txt"
        self.factory_values1 = []
        self.factory_values2 = []
        self.get_start_data()
        self.error=tk.StringVar()
        pad_x= 20
        pad_y = 20
        tk.Label(self,text="Calibration Inputs:",fg="white", font=FONT, bg=GREEN, pady=4).grid(row=0,column=0, columnspan=5, sticky='nsew', pady=4, padx=10)
        tk.Label(self,text="0 value (V): ", font=FONT, fg="black").grid(row=2,column=0, padx=pad_x, pady=pad_y)
        tk.Label(self,text="span value (V): ", font= FONT, fg="black").grid(row=3,column=0, padx=pad_x, pady=pad_y)
        tk.Label(self,text="calibration gas\nconcentration (ppm)",fg="black", font=FONT).grid(row=4,column=0, padx=pad_x, pady=pad_y)
        tk.Label(self,text="NO",fg=GREEN, font=FONT).grid(row=1,column=1, padx=pad_x, pady=5)
        tk.Label(self,text="NO2",fg=RED, font=FONT).grid(row=1,column=2, padx=pad_x, pady=5)
        #testing stuff out
        #tk.Label(self,textvariable=self.error,fg="black", font=FONT).grid(row=5,column=1, columnspan=3, padx=4, sticky="e")
        #tk.Label(self,text="asdfasdfasdfasdf",fg="black", font=FONT).grid(row=5,column=1, columnspan=3, padx=4, sticky="e")
        self.NO_E1 = tk.Entry(self, width=6, font=FONT)
        self.NO_E1.grid(row=2, column=1, padx=pad_x, pady=pad_y)
        self.NO_E1.insert(0,self.bno)
        self.NO_E2 = tk.Entry(self, width=6, font=FONT)
        self.NO_E2.grid(row=3, column=1, padx=pad_x, pady=pad_y)
        self.NO_E2.insert(0, self.span)
        self.NO2_E1 = tk.Entry(self, width=6, font=FONT)
        self.NO2_E1.insert(0, self.bno2)
        self.NO2_E1.grid(row=2, column=2, padx=pad_x, pady=pad_y)
        self.NO2_E2 = tk.Entry(self, width=6, font=FONT)
        self.NO2_E2.insert(0, self.span2)
        self.NO2_E2.grid(row=3, column=2, pady=4)
        self.NO_E3 = tk.Entry(self, width=6, font=FONT)
        self.NO_E3.grid(row=4, column=1, padx=pad_x, pady=pad_y)
        self.NO_E3.insert(0, self.cno)
        self.NO2_E3 = tk.Entry(self, width=6, font=FONT)
        self.NO2_E3.grid(row=4, column=2, padx=pad_x, pady=pad_y)
        self.NO2_E3.insert(0, self.cno2)
        tk.Label(self,text="Get Span", font=FONT, pady=10).grid(row=3,column=3)
        tk.Button(self, text='Get 0', fg="white", bg=GREEN, font=FONT, command=lambda: self.update_start_data("start"), relief='flat').grid(row=2,column=3, pady=pad_y, columnspan=2, sticky="ew")
        tk.Button(self, fg="white", font=FONT, padx=1, width=4, bg=GREEN, text='NO', command=lambda: self.update_start_data("end1"), relief='flat').grid(row=3, column=4, sticky="w", pady=pad_y)
        tk.Button(self, fg="white", bg=GREEN, padx=1, width=4, font=FONT, text='NO2', command=lambda: self.update_start_data("end2"), relief='flat').grid(row=3, column=4, sticky="e", pady=pad_y)
        tk.Button(self, fg="white", bg=GREEN, text='Submit', font=FONT, command=lambda: self.update_start_data("submit"), relief='flat').grid(row=4, column=4, padx=pad_x, pady=pad_y)
        tk.Button(self, text='Log', fg="white", bg=GREEN, font=FONT, command=self.log_start_data, relief='flat').grid(row=4, column=3, padx=pad_x, pady=pad_y)
    
    def update_start_data(self, mode):
        no_val = DAQC2.getADC(addr,0)
        no2_val = DAQC2.getADC(addr,1)
        
        #what to do if "get 0" is pressed
        if mode == "start":
            self.bno = no_val
            self.bno2 = no2_val
            self.NO_E1.delete(0, 'end')
            self.NO_E1.insert(0,self.bno)
            self.NO2_E1.delete(0, 'end')
            self.NO2_E1.insert(0,self.bno2)
            
        #What to do if "NO" is pressed
        if mode == "end1":
            self.span = no_val
            self.span2 = no2_val
            self.NO_E2.delete(0, 'end')
            self.NO_E2.insert(0,self.span)
            
        #What to do if "NO2" is pressed
        if mode == "end2":
            self.span = no_val
            self.span2 = no2_val
            self.NO2_E2.delete(0, 'end')
            self.NO2_E2.insert(0,self.span2)
            
        #set class variables from entry boxes
        self.bno =float(self.NO_E1.get())
        self.span=float(self.NO_E2.get())
        self.bno2=float(self.NO2_E1.get())
        self.span2=float(self.NO2_E2.get())
        self.cno=float(self.NO_E3.get())
        self.cno2=float(self.NO2_E3.get())
        
        #Write to file for value storage
        file = open(self.openfile,'w')
        self.factory_values1[1] = self.bno
        self.factory_values1[2] = self.span
        self.factory_values1[3] = self.cno
        self.factory_values1[4] = self.bno2
        self.factory_values1[5] = self.span2
        self.factory_values1[6] = self.cno2
        str1 = ('|'.join(map(str, self.factory_values1)))
        file.write(str1)
        file.close()
        
    def get_start_data(self):
        #Read in calibtration vlaues from file
        with open(self.openfile,'r') as file:
            fline=file.readline()
            self.factory_values1=fline.split("|")
            self.bno=float(self.factory_values1[1])
            self.span=float(self.factory_values1[2])
            self.cno=float(self.factory_values1[3])
            self.bno2=float(self.factory_values1[4])
            self.span2=float(self.factory_values1[5])
            self.cno2=float(self.factory_values1[6])
            
    def log_start_data(self):
        outfile = "cal-data.csv"
        if not os.path.isfile(outfile):
            with open(outfile,'a+') as f:
                header = "BNO, SPAN NO, CNO, BNO2, SPAN NO2, CNO2\n"
                f.write(header)
        with open(outfile,'a+') as f:
            data = [self.bno, self.span, self.cno, self.bno2, self.span2, self.cno2]
            data_str=','.join(map(str, data))
            f.write(data_str+"\n")
#Create Tabs
class TabManager(tk.Frame):
    
    def __init__(self, parent, *args,  **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        
        #Create Notebook Object
        self.notebook = ttk.Notebook(style='TNotebook')
        
        #Create Tabs
        self.dashboard_tab = tk.Frame(self.notebook)
        self.readings_tab = tk.Frame(self.notebook)
        
        #Add Tabs to Notebook 
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.readings_tab, text="Readings")
        
        self.notebook.pack(side="top", anchor="nw")

#Closes window
def callback():
    app.destroy()
    
def handle_open(event):
    cmd = "./close-keyboard.sh"
    os.system(cmd)
    cmd = "matchbox-keyboard -s 30 numpad-small&"
    os.system(cmd)

def handle_close(event):
    cmd = "./close-keyboard.sh"
    os.system(cmd)
    
app = tk.Tk()
app.title("LANOR Dashboard")
app.geometry("600x440+10+0")
app.wm_protocol("WM_DELETE_WINDOW", callback)
app.configure(background="white")


theme=ttk.Style(app)
theme.configure('.', background="white")
theme.configure('TNotebook.Tab', padding=[2,1], font="black")
theme.map('TNotebook.Tab', foreground=[("selected", BLUE)])
theme.configure('TNotebook', borderwidth=0)

TAB_MANAGER = TabManager(app)
TAB_MANAGER.pack()
lanor = LANOR(TAB_MANAGER.dashboard_tab)
lanor.pack(fill=tk.BOTH, expand=True)
READINGS = Readings(TAB_MANAGER.readings_tab)
READINGS.pack(fill=tk.BOTH, expand=True)


app.mainloop()
                
initADDR3()