#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com
2016

"""

import math, time, scipy
from numpy.random import *
from distutils.dir_util import mkpath
from graph_tool.all import *

# a wrapper for a simple two-dimensional matrix with some convenience functions
class AgentMatrix:
	def __init__(self, width, height, initValue):
		self.matrix = []
		self.width = width
		self.height = height
		self.matrix = [[initValue for x in range(width)] for x in range(height)]

	def getCoords(self):
		coords = [(x,y) for x in range(self.width) for y in range(self.height)]
		return coords
		
	def getShuffledCoords(self):
		coords = [(x,y) for x in range(self.width) for y in range(self.height)]
		shuffle(coords)
		return coords

	def getAt(self, coords):
		x,y = coords[0],coords[1]
		return self.matrix[x][y]

	def setAt(self, coords, value):
		x,y = coords[0],coords[1]
		self.matrix[x][y] = value
	
	def getAgentCount(self):
		return self.width * self.height

# a wrapper for the graph-tool's property maps
class PropertyMap:
	def __init__(self, graph, propertyType, initValue):
		self.myGraph = graph
		self.myPropertyMap = graph.new_vertex_property(propertyType) # e.g. "double"
		for v in graph.vertices():
			self.myPropertyMap[v] = initValue

	def getCoords(self):
		coords = []
		for v in self.myGraph.vertices():
			coords.append(int(v))
		return coords
		
	def getShuffledCoords(self):
		coords = self.getCoords()
		shuffle(coords)
		return coords

	def getAt(self, vertex):
		return self.myPropertyMap[vertex]

	def setAt(self, vertex, value):
		self.myPropertyMap[vertex] = value
	
	def getAgentCount(self):
		return self.myGraph.num_vertices()


class SimManager:
	
	def __init__(self):

		self.running = 0
		self.tick = 0
		
		self.grammar = []
		self.memory = []
		
		self.amplitude = []
		self.amplitudeMemory = []
		
		# the following values are set through the config file
		self.gridSize = 0
		self.width = 0
		self.height = 0
		
		# how likely the agent is to change its behaviour; 0.2: slow change, 0.8: fast change, 0.5: default
		self.lambdaValue = 0 
		
		#10: very fast change, 100: very slow change
		self.memorySize = 0 
		
		# fitness of alpha, bias towards alpha (if given a choice between alpha and beta)
		self.alphaBias = 0 
		self.errorRate = 0
		self.utteranceLength = 0
		self.discreteProduction = False
		self.waveAmplitude = 0
		self.timesteps = 0

		self.logValues = []
		self.outputDir = ""
		self.startTime = 0
		self.graphMode = False


	def setOutputDir(self, s):
		self.outputDir = s

	def setGridSize(self, s):
		self.gridSize = s
		self.width = s
		self.height = s

	def setLambdaValue(self, i):
		self.lambdaValue = i

	def setAlphaBias(self, i):
		self.alphaBias = i

	def setMemorySize(self, i):
		self.memorySize = i

	def setErrorRate(self, i):
		self.errorRate = i

	def setUtteranceLength(self, i):
		self.utteranceLength = i

	def setDiscreteProduction(self, i):
		self.discreteProduction = i

	def setWaveAmplitude(self, i):
		self.waveAmplitude = i

	def setTimesteps(self, i):
		# this is actually not used during the simulation, but it's needed for exporting the simulation parameters when writing to the log file
		self.timesteps = i

	def initSim(self):
		self.tick = 0
		self.startTime = time.time()
		
		self.grammar = AgentMatrix(self.width, self.height, 0)
		self.memory = AgentMatrix(self.width, self.height, "")
		self.amplitude = AgentMatrix(self.width, self.height, 0)
		self.amplitudeMemory = AgentMatrix(self.width, self.height, [])
		
		# numpy arrays; turns out to be slower, though
		#~ self.grammarMatrix = scipy.empty((self.width, self.height))
		#~ self.memoryMatrix = numpy.array([['' for x in range(self.width)] for x in range(self.height)], dtype="U10") # data type: Unicode, string length 10
	
		# define an innovator in the middle of the grid
		i = int(self.gridSize/2)
		self.grammar.setAt((i,i), 1)
		if self.waveAmplitude > 0: 
			self.amplitude.setAt((i,i), self.waveAmplitude)
		
		# color property
		self.colors = AgentMatrix(self.gridSize, self.gridSize, 0)
		for coords in self.colors.getCoords():
			newColor = self.calculateColor(self.grammar.getAt(coords))
			self.colors.setAt(coords, newColor)
		
		print("simulation initiated.")

	def initSimFromGraph(self, graph, pos):
		self.tick = 0
		self.startTime = time.time()
		self.graphMode = True
		
		self.myGraph, self.pos = graph, pos
				
		self.grammar = PropertyMap(graph, "double", 0)
		self.memory = PropertyMap(graph, "string", "")
		self.amplitude = PropertyMap(graph, "double", 0)
		self.amplitudeMemory = PropertyMap(graph, "double", 0)

		# define an innovator in the middle of the grid
		self.grammar.setAt(0, 1)
		if self.waveAmplitude > 0: 
			self.amplitude.setAt(0, self.waveAmplitude)

		# color property
		self.colors = PropertyMap(graph, "vector<double>", [])
		for coords in self.colors.getCoords():
			newColor = self.calculateColor(self.grammar.getAt(coords))
			self.colors.setAt(coords, newColor)
		
		print("simulation initiated.")

	def calculateColor(self, grammarValue):
		red = 1 - grammarValue
		green = 0.5 * grammarValue # forest green
		blue = 0
		alpha = 1
		return [red, green, blue, alpha]

	def stepSim(self):
		sumGValues = 0
		for thisAgent in self.grammar.getShuffledCoords():
			#pick a neighbor
			if self.graphMode:
				neighbor = self.getRandomNeighborGraphMode(thisAgent)
			else:
				neighbor = self.getRandomNeighbor(thisAgent)
				
			self.communicate(thisAgent, neighbor)

			# wave amp of speaker should decay a little
			speakerAmp = self.amplitude.getAt(thisAgent)
			speakerAmp = speakerAmp * 0.95
			if speakerAmp < 0.01: speakerAmp = 0
			self.amplitude.setAt(thisAgent, speakerAmp)
			
			# update colors
			newColor = self.calculateColor(self.grammar.getAt(thisAgent))
			self.colors.setAt(thisAgent, newColor)
			sumGValues += self.grammar.getAt(thisAgent)
			
		# save indexed values for later export (e.g. for plotting in R)
		sumAgents = self.grammar.getAgentCount()
		alpha_y = 100 / sumAgents * sumGValues
		beta_y = 100 / sumAgents * (sumAgents - sumGValues)
		self.logValues.append([self.tick, alpha_y, beta_y])
		
		self.tick += 1

# find a neighbor, does not need to be direct neighbor but up to n positions away
# closer ones should be more likely to be chosen
	def getRandomNeighbor(self, thisAgent):
		dist = 0
		max_dist = 5
		currentAgent = thisAgent
		thisNeighbor = 0
		# retry if coords are out of bounds
		while True:
			thisNeighbor = self.moveCoords(currentAgent)
			if self.isValidNeighbor(thisAgent, thisNeighbor):
				dist += 1
				if randint(0,2) == 1 or dist >= max_dist: return thisNeighbor
				currentAgent = thisNeighbor

	# input: pair of coords, output: coords of a randomly chosen bordering neighbor ( 4 possibilities: up, right, down, left) 
	def moveCoords(self, coords):
		v, w = coords
		i = randint(0,4) # 0..3
		if i == 0: v -= 1
		elif i == 1: v += 1
		elif i == 2: w -= 1
		elif i == 3: w += 1
		return (v, w)

	# check if the selected neighbor is valid by making sure it is a) within bounds and 2) not identical to the original agent (the algorithm could step back to the starting point after the second move)
	def isValidNeighbor(self, thisAgent, thisNeighbor):
		x,y = thisNeighbor
		if thisAgent == thisNeighbor: return False
		if x < 0 or y < 0: return False
		if x >= self.width or y >= self.height: return False
		return True

	def getRandomNeighborGraphMode(self, thisAgent):
		neighbors = list(self.myGraph.vertex(thisAgent).out_neighbours())
		if len(neighbors) > 0:
			neighbor = neighbors[randint(0, len(neighbors))]  # choose a random neighbour
		return neighbor


	def communicate(self, agent, neighbor):
		utteranceAgent = self.produceUtterance(agent)
		utteranceNeighbor = self.produceUtterance(neighbor)
		
		if self.waveAmplitude > 0:
			self.updateAmplitude(utteranceAgent, agent, neighbor)
			self.updateAmplitude(utteranceNeighbor, neighbor, agent)
			#~ print("all amplitude: " + str(self.amplitude.matrix))
			#~ print("all amplitudeMemory: " + str(self.amplitudeMemory.matrix))
		
		oldGrammar = self.grammar.getAt(agent)
		oldMemory = self.memory.getAt(agent)

		#store in memory
		self.memory.setAt(agent, self.truncateMemory(utteranceNeighbor + self.memory.getAt(agent)))
		self.memory.setAt(neighbor, self.truncateMemory(utteranceAgent + self.memory.getAt(neighbor)))

		# calculate new grammar values
		agentGrammarNew = self.grammar.getAt(agent) + self.lambdaValue * (self.countARatio(self.memory.getAt(agent)) - self.grammar.getAt(agent))
		neighborGrammarNew = self.grammar.getAt(neighbor) + self.lambdaValue * (self.countARatio(self.memory.getAt(neighbor)) - self.grammar.getAt(neighbor))

		agentGrammarNew = round(agentGrammarNew, 10)
		neighborGrammarNew = round(neighborGrammarNew, 10)
		
		if self.discreteProduction:
			self.grammar.setAt(agent, 0 if (agentGrammarNew <= 0.5) else 1)
			self.grammar.setAt(neighbor, 0 if (neighborGrammarNew <= 0.5) else 1)
		else:
			self.grammar.setAt(agent, agentGrammarNew)
			self.grammar.setAt(neighbor, neighborGrammarNew)

	def produceUtterance(self, agent):
		ulist = []
		bias = self.alphaBias
		if self.waveAmplitude > 0: # we are operating in the wave scenario
			bias = self.amplitude.getAt(agent)
			#~ print("producing now with bias=" + str(bias))

		adjusted_g = self.grammar.getAt(agent) * (1 + bias)
		#~ print("g=" + str(self.grammar.getAt(agent)))
		#~ print("producing now with adjusted_g=" + str(adjusted_g))
		for i in range(self.utteranceLength):
			myRand = random()
			# if we are operating in the wave scenario, use the wave amplitude instead of the global bias
			if (myRand <= adjusted_g): ulist.append("α")
			else: ulist.append("β")
		return ''.join(ulist)

	def countARatio(self, memory):
		if len(memory) == 0: return 0
		return memory.count('α')/len(memory)

	def truncateMemory(self, memory):
		return memory[:self.memorySize]

	def updateAmplitude(self, utterance, speaker, hearer):
		if "α" in utterance:
			amp = self.amplitude.getAt(speaker) #* 0.9 # dampen the amplitude
			if amp > 0.01: #ignore very small amplitudes
				# only remember first amp value and remember it 
				m = self.amplitudeMemory.getAt(hearer)
				if m == []:
					self.amplitudeMemory.setAt(hearer, amp)
					self.amplitude.setAt(hearer, amp)

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
		mkpath("./" + self.outputDir)
		
		# write log of this simulation run
		logFileName = str(self.outputDir + 'simulation.log')
		f = open(logFileName, 'w')
		f.write("logfile timestamp: " + time.strftime("%Y-%m-%d %H:%M:%S") + '\n')
		delta = time.time() - self.startTime
		m, s = divmod(delta, 60)
		h, m = divmod(m, 60)
		f.write("elapsed time: %d hours, %d minutes, %f seconds" % (h, m, s)) 
		# note that this will depend on other work load on the machine, as well
		f.write("\n\nparameters used:\n") 
		f.write("gridSize=" + str(self.gridSize) + '\n') 
		f.write("lambdaValue=" + str(self.lambdaValue) + '\n') 
		f.write("memorySize=" + str(self.memorySize) + '\n') 
		f.write("alphaBias=" + str(self.alphaBias) + '\n') 
		f.write("errorRate=" + str(self.errorRate) + '\n') 
		f.write("utteranceLength=" + str(self.utteranceLength) + '\n') 
		f.write("discreteProduction=" + str(self.discreteProduction) + '\n') 
		f.write("waveAmplitude=" + str(self.waveAmplitude) + '\n') 
		f.write("timesteps=" + str(self.timesteps) + '\n') 
		f.close()
		
		# export the sums of the g values, in a CSV format to be processed by e.g. R
		datFileName = str(self.outputDir + 'frequencies.dat')
		f = open(datFileName, 'w')
		f.write("Ticks,AlphaY,BetaY\n")
		for i in range(len(self.logValues)):
			a = self.logValues[i]
			f.write(str(a[0]) + "," + str(a[1]) + "," + str(a[2]) + "\n")
		f.close()
		
		#numpy.set_printoptions(threshold=numpy.inf)
		grammarFileName = str(self.outputDir + "grammar.dat")
		f = open(grammarFileName, 'w')
		for v in self.grammar.getCoords():
			f.write(str(self.grammar.getAt(v)) + "\n")
		f.close()
		memoryFileName = str(self.outputDir + "memory.dat")
		f = open(memoryFileName, 'w')
		for v in self.grammar.getCoords():
			f.write(str(self.memory.getAt(v)) + "\n")
		f.close()
		amplitudeFileName = str(self.outputDir + "amplitude.dat")
		f = open(amplitudeFileName, 'w')
		for v in self.grammar.getCoords():
			f.write(str(self.amplitude.getAt(v)) + "\n")
		f.close()




