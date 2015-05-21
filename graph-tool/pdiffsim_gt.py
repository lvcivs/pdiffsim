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
nogui = config.getboolean('simulation', 'nogui')
runs = config.getint('simulation', 'runs')


myGraph, pos = triangulation(random((speakers, 2)) * 4, type="delaunay") # will create a more or less rectangular layout
simManager.initSim(myGraph, pos)



# This creates a GTK+ window with the initial graph layout
if nogui:
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

#~ win.graph.regenerate_surface(lazy=False)
#~ win.graph.queue_draw()

dirName = logFileName + '/'
mkpath("./" + dirName)

exportedFirst = False
running = True
		
		
# This function will be called repeatedly by the GTK+ main loop
def update_state_gui():

	simManager.stepSim()

	win.graph.regenerate_surface(lazy=False)
	win.graph.queue_draw()
	
	#~ # save a screenshot of the GTK window
	#~ width, height = win.get_size()
	#~ pixbuf = Gdk.Pixbuf(Gdk.COLORSPACE_RGB, False, 8, width, height)
#~ 
	#~ screenshot = pixbuf.get_from_drawable(win.window, win.get_colormap(), 
																				#~ 0, 0, 0, 0, width, height)
	#~ screenshot.save(logFileName + '/screenshot.png', 'png')
	
	return True

# This function will be called repeatedly by the GTK+ main loop
def update_state_nogui():
	global exportedFirst
	global running
	
	
	if not exportedFirst:
		pixbuf = win.get_pixbuf()
		pixbuf.savev(logFileName + '/frame00.png', 'png', [], [])
		exportedFirst = True
		return True
	
	if not running:
		pixbuf = win.get_pixbuf()
		pixbuf.savev(logFileName + '/frameZZ.png', 'png', [], [])
		sys.exit(0)

	# run through all of the simulation
	for i in range(runs):
		simManager.stepSim()
	simManager.exportData()
	print("done running the simulation. exported data.")
	running = False
	
	win.graph.regenerate_surface(lazy=False)
	win.graph.queue_draw()

	return True


# Bind the function above as an 'idle' callback.
if nogui:
	cid = GObject.idle_add(update_state_nogui)
else:
	cid = GObject.idle_add(update_state_gui)


# We will give the user the ability to stop the program by closing the window.
win.connect("delete_event", Gtk.main_quit)

# Actually show the window, and start the main loop.
win.show_all()
Gtk.main()
