#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com

"""

import sys, os, os.path, math
from numpy.random import *
from distutils.dir_util import mkpath
import configparser
from graph_tool.all import *


# We need some Gtk and gobject functions
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from simmanager_gt import SimManager


if len(sys.argv) == 1 : 
	print("No config file specified.\nUsage: pdiffsym_gt.py [Config File]")
	sys.exit(0)

simManager = SimManager()
logFileName = str(sys.argv[1])[:-4] + ".log"
simManager.setLogFileName(logFileName)

# Read config file
config = configparser.ConfigParser()
config.read(sys.argv[1])

speakers = config.getint('simulation', 'speakers')
simManager.setSpeakers(speakers)
simManager.setLambdaValue(config.getfloat('simulation', 'lambdaValue'))
simManager.setMemorySize(config.getint('simulation', 'memorySize'))
simManager.setAlphaBias(config.getfloat('simulation', 'alphaBias'))
simManager.setErrorRate(config.getfloat('simulation', 'errorRate'))
simManager.setUtteranceLength(config.getint('simulation', 'utteranceLength'))
gui = config.getboolean('simulation', 'gui')
runs = config.getint('simulation', 'runs')


myGraph, pos = triangulation(random((speakers, 2)) * 4, type="delaunay") # will create a more or less rectangular layout
simManager.initSim(myGraph, pos)



# This creates a GTK+ window with the initial graph layout
if not gui:
	win = Gtk.OffscreenWindow()
	win.set_default_size(500, 400)
	win.graph = GraphWidget(simManager.myGraph, simManager.pos,
													edge_color=[0.6, 0.6, 0.6, 1],
													vertex_fill_color=simManager.colors)
	win.add(win.graph)


else:
	win = GraphWindow(simManager.myGraph, simManager.pos, geometry=(500, 400),
										edge_color=[0.6, 0.6, 0.6, 1],
										vertex_fill_color=simManager.colors)

win.graph.regenerate_surface(lazy=False)
win.graph.queue_draw()

dirName = logFileName + '/'
mkpath("./" + dirName)

graphDirty = True
		
		
# This function will be called repeatedly by the GTK+ main loop
def update_state_gui():

	simManager.stepSim()

	win.graph.regenerate_surface(lazy=False)
	win.graph.queue_draw()
	
	#~ gtk.Widget.get_snapshot() 
	 
	return True

# works, but slow
def update_state_nogui():
	global graphDirty
	
	if simManager.tick >= runs - 1:
		simManager.exportData()
		print("done running the simulation. exported data.")
		sys.exit(0)

	# run through all of the simulation
	simManager.stepSim()
	graphDirty = True
	
	win.graph.regenerate_surface(lazy=False)
	win.graph.queue_draw()

	return True

def saveScreenshot(s, e):
	global graphDirty
	if graphDirty:
		pixbuf = win.get_pixbuf()
		pixbuf.savev(logFileName + '/frame' + str(simManager.tick).zfill(4) + '.png', 'png', [], [])
		graphDirty = False
		print("saving screenshot " + str(simManager.tick))

# Bind the function above as an 'idle' callback.
if not gui:
	cid = GObject.idle_add(update_state_nogui)
else:
	cid = GObject.idle_add(update_state_gui)
#~ win.connect_after("draw", saveScreenshot)
win.connect_after("damage-event", saveScreenshot)

# We will give the user the ability to stop the program by closing the window.
win.connect("delete_event", Gtk.main_quit)

# Actually show the window, and start the main loop.
win.show_all()
Gtk.main()
