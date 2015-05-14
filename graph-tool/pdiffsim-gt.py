#! /usr/bin/env python
# -*- coding: utf-8 -*-


from graph_tool.all import *
from numpy.random import *
import sys, os, os.path, math


seed(42)
seed_rng(42)

count = 0

# We need some Gtk and gobject functions
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

# We will use the network of network scientists, and filter out the largest
# component
#~ g = collection.data["netscience"]
#~ g = collection.data["dolphins"]
#~ pos = g.vp["pos"]  # layout positions

#~ g = random_graph(1600, lambda: 1 + poisson(4), directed=False) # second argument is the degree sampler function (≈ average of 5 connections per node)
#~ pos = sfdp_layout(g) # spread out the nodes in space according to this algorithm
#~ pos = arf_layout(g) # spread out the nodes in space according to this algorithm
#~ g = collection.data["netscience"]
g, pos = triangulation(random((1600, 2)) * 4, type="delaunay") # will create a more or less rectangular layout
max_count = 501


# Initialize 
grammar = g.new_vertex_property("double")
memory = g.new_vertex_property("string")
for v in g.vertices():
	grammar[v] = 0
	memory[v] = ""

#innovator
grammar[g.vertex(0)] = 1

# color property
colors = g.new_vertex_property("vector<double>")
def calculateColor(g):
	red = 1 - g
	green = 0.5 * g # forest green
	blue = 0
	alpha = 1
	return [red, green, blue, alpha]

for v in g.vertices():
	colors[v] = calculateColor(grammar[v])

# If True, the frames will be dumped to disk as images.
offscreen = sys.argv[1] == "offscreen" if len(sys.argv) > 1 else False
if offscreen and not os.path.exists("./frames"):
		os.mkdir("./frames")



# This creates a GTK+ window with the initial graph layout
if not offscreen:
		win = GraphWindow(g, pos, geometry=(500, 400),
											edge_color=[0.6, 0.6, 0.6, 1],
											vertex_fill_color=colors)
else:
		win = Gtk.OffscreenWindow()
		win.set_default_size(500, 400)
		win.graph = GraphWidget(g, pos,
														edge_color=[0.6, 0.6, 0.6, 1],
														vertex_fill_color=colors)
		win.add(win.graph)

# sim stuff
def communicate(agent, neighbor):
	utteranceAgent = produceUtterance(agent)
	utteranceNeighbor = produceUtterance(neighbor)
	
	#store in memory
	memory[agent] = truncateMemory(utteranceNeighbor + memory[agent])
	memory[neighbor] = truncateMemory(utteranceAgent + memory[neighbor])
	
	# adapt grammar
	lambdaValue = 0.5

	agentGrammarNew = grammar[agent] + lambdaValue * (countARatio(memory[agent]) - grammar[agent])
	neighborGrammarNew = grammar[neighbor] + lambdaValue * (countARatio(memory[neighbor]) - grammar[neighbor])

	agentGrammarNew = round(agentGrammarNew, 10)
	neighborGrammarNew = round(neighborGrammarNew, 10)
	
	grammar[agent] = agentGrammarNew
	grammar[neighbor] = neighborGrammarNew


def produceUtterance(agent):
	alphaBias = 1.025
	u = ""
	for i in range(10):
		myRand = random()
		if (myRand <= grammar[agent] * alphaBias): u += "α" # bias is implemented by multiplication
		else: u += "β"
	return u

def countARatio(memory):
	return memory.count('α')/len(memory)

def truncateMemory(memory):
	return memory[:20]
	
		
# This function will be called repeatedly by the GTK+ main loop, and we use it
# to update the state according to the SIRS dynamics.
def update_state():
	#~ newly_infected.a = False
	global count
	print (count)

	# visit the nodes in random order
	vs = list(g.vertices())
	shuffle(vs)
	for v in vs:
		#~ print (grammar[v])
		#~ print (memory[v])

		#pick a neighbor
		neighbors = list(v.out_neighbours())
		if len(neighbors) > 0:
			neighbor = neighbors[randint(0, len(neighbors))]  # choose a random neighbour
		communicate(v, neighbor)

		# update colors
		colors[v] = calculateColor(grammar[v])

	# only record every n-th step
	if (count%10==1):
		# The following will force the re-drawing of the graph, and issue a
		# re-drawing of the GTK window.
		win.graph.regenerate_surface(lazy=False)
		win.graph.queue_draw()

		# if doing an offscreen animation, dump frame to disk
		if offscreen:
				#~ global count
				pixbuf = win.get_pixbuf()
				pixbuf.savev(r'./frames/sirs%06d.png' % count, 'png', [], [])
	if count > max_count:
		sys.exit(0)
	count += 1

	# We need to return True so that the main loop will call this function more
	# than once.
	return True


# Bind the function above as an 'idle' callback.
cid = GObject.idle_add(update_state)

# We will give the user the ability to stop the program by closing the window.
win.connect("delete_event", Gtk.main_quit)

# Actually show the window, and start the main loop.
win.show_all()
Gtk.main()
