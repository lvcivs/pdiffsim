#! /usr/bin/env python
# -*- coding: utf-8 -*-


from graph_tool.all import *
from numpy.random import *
import sys, os, os.path, math, configparser

# We need some Gtk and gobject functions
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from simmanager_gt import SimManager


if len(sys.argv) == 1 : 
	print("No config file specified.\nUsage: pdiffsym_gt.py [Config File]")
	sys.exit(0)

# Read config file
config = configparser.ConfigParser()
config.read(sys.argv[1])

simManager = SimManager()
logFileName = str(sys.argv[1])[:-4] + ".log"
simManager.setLogFileName(logFileName)
speakers = config.getint('simulation', 'speakers')
simManager.setSpeakers(speakers)
#~ simManager.setInitScenario(config.get('simulation', 'initScenario'))
simManager.setLambdaValue(config.getfloat('simulation', 'lambdaValue'))
simManager.setMemorySize(config.getint('simulation', 'memorySize'))
simManager.setAlphaBias(config.getfloat('simulation', 'alphaBias'))
simManager.setErrorRate(config.getfloat('simulation', 'errorRate'))
#~ simManager.setNeighborRange(config.getint('simulation', 'neighborRange'))
simManager.setUtteranceLength(config.getint('simulation', 'utteranceLength'))
nogui = config.getboolean('simulation', 'nogui')
#~ interactive = config.getboolean('simulation', 'interactive')
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

	for i in range(runs):
		simManager.stepSim()
	simManager.exportData()
	print("done running the simulation. exported data.")

	
else:
	win = GraphWindow(simManager.myGraph, simManager.pos, geometry=(500, 400),
										edge_color=[0.6, 0.6, 0.6, 1],
										vertex_fill_color=simManager.colors)

#~ win.graph.regenerate_surface(lazy=False)
#~ win.graph.queue_draw()



running = True
exportedFirst = False

		
		
# This function will be called repeatedly by the GTK+ main loop
def update_state_gui():

	simManager.stepSim()

	win.graph.regenerate_surface(lazy=False)
	win.graph.queue_draw()
	
	#~ width, height = win.get_size()
	#~ pixbuf = Gdk.Pixbuf(Gdk.COLORSPACE_RGB, False, 8, width, height)
#~ 
	#~ screenshot = pixbuf.get_from_drawable(win.window, win.get_colormap(), 
																				#~ 0, 0, 0, 0, width, height)
	#~ screenshot.save(logFileName + '/screenshot.png', 'png')
	
	return True

# This function will be called repeatedly by the GTK+ main loop
def update_state_nogui():
	global running
	global exportedFirst

	if not running: sys.exit(0)
	
	if not exportedFirst:
		pixbuf = win.get_pixbuf()
		pixbuf.savev(logFileName + '/frame00.png', 'png', [], [])
		exportedFirst = True
	else:
		pixbuf = win.get_pixbuf()
		pixbuf.savev(logFileName + '/frameZZ.png', 'png', [], [])
		running = False
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
