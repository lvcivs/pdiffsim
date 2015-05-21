#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com

"""

import math, time, scipy
import scipy.misc as scipymisc
from numpy.random import *
from distutils.dir_util import mkpath
from graph_tool.all import *


class SimManager:
	
	def __init__(self):

		self.myGraph, self.pos = 0, 0

		self.running = 0
		self.tick = 0
		
		self.speakers = 0
		self.lambdaValue = 0.5 # how likely the agent is to change its behaviour; 0.2: slow change, 0.8: fast change, 0.5: default
		self.memorySize = 20 #10: very fast change, 100: very slow change
		self.alphaBias = 1.0 # fitness of alpha, bias towards alpha (if given a choice between alpha and beta)
		self.errorRate = 0
		self.neighborRange = 1
		self.utteranceLength = 10

		self.logFileName = ""
		
		self.startTime = 0
		
		#~ self.visUpdateEvent = Event()

	def setLogFileName(self, s):
		self.logFileName = s
		
	
	def setSpeakers(self, s):
		self.speakers = s
	
	def setLambdaValue(self, i):
		self.lambdaValue = i
		#~ self.visUpdateEvent.fire()
	
	def setAlphaBias(self, i):
		self.alphaBias = i
		#~ self.visUpdateEvent.fire()
	
	def setMemorySize(self, i):
		self.memorySize = i
		#~ self.visUpdateEvent.fire()

	def setNeighborRange(self, i):
		self.neighborRange = i
		#~ self.visUpdateEvent.fire()
	
	def setWeighting(self, s):
		myClassName = ""
		myDisabled = True
		if (s == "none"):
			self.alphaBias = 1
			self.myClassName = "grayed"
			self.myDisabled = True
		elif (s == "weighted"):
			myClassName = ""
			myDisabled = False

	def setErrorRate(self, i):
		self.errorRate = i
		#~ self.visUpdateEvent.fire()
		
	def setUtteranceLength(self, i):
		self.utteranceLength = i
		#~ self.visUpdateEvent.fire()

	def initSim(self, myGraph, pos):
		self.tick = 0
		self.startTime = time.time()

		self.myGraph, self.pos = myGraph, pos

		self.grammar = self.myGraph.new_vertex_property("double")
		self.memory = self.myGraph.new_vertex_property("string")
		
		# Initialize 
		for v in self.myGraph.vertices():
			self.grammar[v] = 0
			self.memory[v] = ""
	
		#innovator
		self.grammar[self.myGraph.vertex(0)] = 1
		
		# color property
		self.colors = self.myGraph.new_vertex_property("vector<double>")
		for v in self.myGraph.vertices():
			self.colors[v] = self.calculateColor(self.grammar[v])

	def calculateColor(self, grammarValue):
		red = 1 - grammarValue
		green = 0.5 * grammarValue # forest green
		blue = 0
		alpha = 1
		return [red, green, blue, alpha]

	#~ def runSim(self): # run or stop
		#~ if not running:
			#~ self.running = 1
		#~ else:
			#~ self.stopSim()
#~ 
	#~ def stopSim(self):
		#~ #clearInterval(interval)
		#~ self.running = 0

	def stepSim(self):
		print("step " + str(self.tick))
		#~ print("step " + str(self.tick) + " .. ", end="")
		vertices = list(self.myGraph.vertices())
		shuffle(vertices)
		for thisVertex in vertices:
			#pick a neighbor
			neighbors = list(thisVertex.out_neighbours())
			if len(neighbors) > 0:
				neighbor = neighbors[randint(0, len(neighbors))]  # choose a random neighbour
			self.communicate(thisVertex, neighbor)

			# update colors
			self.colors[thisVertex] = self.calculateColor(self.grammar[thisVertex])

		self.tick += 1


	def communicate(self, agent, neighbor):
		utteranceAgent = self.produceUtterance(agent)
		utteranceNeighbor = self.produceUtterance(neighbor)
		
		#~ print("said: " + utteranceAgent + ", " + utteranceNeighbor)
		
		#store in memory
		self.memory[agent] = self.truncateMemory(utteranceNeighbor + self.memory[agent])
		self.memory[neighbor] = self.truncateMemory(utteranceAgent + self.memory[neighbor])

		agentGrammarNew = self.grammar[agent] + self.lambdaValue * (self.countARatio(self.memory[agent]) - self.grammar[agent])
		neighborGrammarNew = self.grammar[neighbor] + self.lambdaValue * (self.countARatio(self.memory[neighbor]) - self.grammar[neighbor])

		agentGrammarNew = round(agentGrammarNew, 10)
		neighborGrammarNew = round(neighborGrammarNew, 10)
		
		self.grammar[agent] = agentGrammarNew
		self.grammar[neighbor] = neighborGrammarNew


	
	def produceUtterance(self, agent):
		u = ""
		for i in range(self.utteranceLength):
			myRand = random()
			if (myRand <= self.grammar[agent] * self.alphaBias): u += "α" # bias is implemented by multiplication
			else: u += "β"
		return u

	def countARatio(self, memory):
		if len(memory) == 0: return 0
		return memory.count('α')/len(memory)

	def truncateMemory(self, memory):
		return memory[:self.memorySize]


	def applyError(self, s): # (potentially) introduce misunderstandings between speaker and hearer
		if self.errorRate == 0: return s
		result = ""
		for i in range(len(s)):
			thisChar = s[i]
			thisResultChar = thisChar
			if (random() < self.errorRate):
				# switch them around
				if (thisChar == "β"): thisResultChar = "α"
				else: thisResultChar = "β"
			result += thisResultChar
		return result

	def exportData(self):
		dirName = self.logFileName + '/'
		mkpath("./" + dirName)
		
		# write log of this simulation run
		f = open(dirName + self.logFileName, 'w')
		f.write("logfile timestamp: " + time.strftime("%Y-%m-%d %H:%M:%S") + '\n')
		delta = time.time() - self.startTime
		m, s = divmod(delta, 60)
		h, m = divmod(m, 60)
		f.write("elapsed time: %d hours, %d minutes, %f seconds" % (h, m, s)) 
		# note that this will depend on other work load on the machine, as well
		f.close()
		
		# save indexed values for later export (e.g. for plotting in R)
		sumGValues = 0
		for v in self.myGraph.vertices():
				sumGValues += self.grammar[v]

		sumAgents = self.myGraph.num_vertices()
		alpha_y = 100 / sumAgents * sumGValues
		beta_y = 100 / sumAgents * (sumAgents - sumGValues)
		
		# export the sums of the g values, in a CSV format to be processed by e.g. R
		datFileName = str(dirName + self.logFileName)[:-4] + '.dat'
		f = open(datFileName, 'w')
		f.write("Ticks,AlphaY,BetaY\n")
		f.write(str(self.tick) + "," + str(alpha_y) + "," + str(beta_y) + "\n")
		f.close()
		
		#numpy.set_printoptions(threshold=numpy.inf)
		grammarFileName = str(dirName + "grammar.dat")
		f = open(grammarFileName, 'w')
		for v in self.myGraph.vertices():
			f.write(str(self.grammar[v]) + "\n")
		f.close()
		memoryFileName = str(dirName + "memory.dat")
		f = open(memoryFileName, 'w')
		for v in self.myGraph.vertices():
			f.write(str(self.memory[v]) + "\n")
		f.close()
		#~ 
		#~ # prepare image matrix, save to file
		#~ imageMatrix = numpy.zeros((self.width*4, self.height*4, 3), dtype=numpy.uint8)
		#~ for x in range(self.width):
			#~ for y in range(self.height):
				#~ p = self.grammarMatrix[x][y]
				#~ green = math.floor(128 * p); # green according to CSS color definition
				#~ red = math.floor(255 * (1 - p))
				#~ thisColor = [red, green, 0]
				#~ imgX = x * 4
				#~ imgY = y * 4
				#~ for i in range(4): imageMatrix[imgY+i][imgX:imgX+4] = thisColor
		#~ img = scipymisc.toimage(imageMatrix)
		#~ imgFileName = str(dirName + "final.png")
		#~ scipymisc.imsave(imgFileName, img)



