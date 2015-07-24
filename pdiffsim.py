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

from simmanager import SimManager


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
network = config.get('simulation', 'network')
simManager.setSpeakers(speakers)
simManager.setLambdaValue(config.getfloat('simulation', 'lambdaValue'))
simManager.setMemorySize(config.getint('simulation', 'memorySize'))
simManager.setAlphaBias(config.getfloat('simulation', 'alphaBias'))
simManager.setErrorRate(config.getfloat('simulation', 'errorRate'))
simManager.setUtteranceLength(config.getint('simulation', 'utteranceLength'))
simManager.setDiscreteProduction(config.getboolean('simulation', 'discreteProduction'))
simManager.setWaveAmplitude(config.getfloat('simulation', 'waveAmplitude'))
snapshotInterval = config.getint('simulation', 'snapshotInterval')
gui = config.getboolean('simulation', 'gui')
runs = config.getint('simulation', 'runs')


if network == "random":
	myGraph, pos = triangulation(random((speakers, 2)) * 4, type="delaunay") # will create a more or less rectangular layout
else:
	myGraph = collection.data[network] #~ "netscience", "dolphins", ...
	pos = myGraph.vp["pos"]
	
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

win.graph.regenerate_surface()
win.graph.queue_draw()

dirName = logFileName + '/'
mkpath("./" + dirName)

# this will keep track if there have been any changes that require a redraw 
graphDirty = True

# This function will be called repeatedly by the GTK+ main loop
def update_state_gui():

	simManager.stepSim()

	win.graph.regenerate_surface()
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

	# advance the simulation by one step
	simManager.stepSim()
	graphDirty = True
	
	win.graph.regenerate_surface()
	win.graph.queue_draw()

	return True

def saveSnapshot(s, e):
	global graphDirty
	if graphDirty and (simManager.tick % snapshotInterval == 0):
		pixbuf = win.get_pixbuf()
		pixbuf.savev(logFileName + '/frame' + str(simManager.tick).zfill(4) + '.png', 'png', [], [])
		graphDirty = False

# set up the callback functions
if not gui:
	cid = GObject.timeout_add(400, update_state_nogui) # time in milliseconds [if we go too low there won't be enough time to update the offscreen window and save snapshots]
	# for a small network of 200, a small value of 200 should be enough
	# for a large network of 2000 agents, this value should be 500 or more
else:
	cid = GObject.idle_add(update_state_gui)
win.connect_after("damage-event", saveSnapshot)

# close the window on user request
win.connect("delete_event", Gtk.main_quit)

# show the window, and start the main loop
win.show_all()
Gtk.main()
