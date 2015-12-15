# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 21:41:47 2015
Project: Stock Trading 
@author: Peter Lee

Note: use os.system('command') to call system command
"""

project = "Stock Trading @ Data Incubator"
folder = "D:\\workspace"

import os, re, sys, datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Environmental variables
envScriptName = sys.argv[0]
envSystem = os.name
os.chdir(folder)     # Change dir to the working folder
print "--- Environmental Variables ---"
print "Script Name: " + envScriptName
print "Working Folder (%s files): %s" % (str(len(os.listdir(folder))), os.getcwd())
print "Operating System : %s" % os.name

# Define the Log File
log_called = False
def log(*texts):
    '''
    Saves strings into a log file, in the user-defined folder.
    If receives multiple arguments, each argument is saved into a separate line.
    If the log file does not exist, a new log file is created with headers.
    
    Parameters
    ----------
    *texts: one or more string arguments.
    
    Returns
    -------
    None
    
    '''
    global log_called 
    for txt in texts:
        # check if log has been called
        if log_called == False:            
            # check if log folder exists
            if not os.path.exists(folder):
                if envSystem=='nt':                
                    os.system("md %s" % folder)
                else:
                    print "Error: The log file direction does not exist!"
                    sys.exit(1)
                print "A new folder \"%s\" is created because it does not exist." % folder
            else: 
                # check if log file exists
                if os.path.exists(folder + "//log.txt"):
                    print "A new log is created (file \"%s//log.txt\" is over-written)." % folder
                else:
                    log_default = open(folder + "//log.txt", 'w')
                    log_default.write("LOG FILE\n\r")
                    log_default.write("Project: %s\n\r" % project)
                    log_default.write("Author: Peter Lee (mr.peter.lee@hotmail.com)\n\r")
                    log_default.write("Date Created: %s\n\r" % str(datetime.datetime.now()) )
                    log_default.write("\n\r\n\r")
                    log_default.write(txt + "\n\r")
                    log_default.close()
                    log_called = True
        else:
            log_default = open(folder + "//log.txt", 'a')
            log_default.write(txt + "\n\r")
            log_default.close()
            log_called = True

# Main Program 
log("fuck how old ar eyou?")