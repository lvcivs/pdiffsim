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
		
		# the following values are set through the config file
		self.speakers = 0
		
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

		self.logValues = []
		self.logFileName = ""
		self.startTime = 0


	def setLogFileName(self, s):
		self.logFileName = s
		
	
	def setSpeakers(self, s):
		self.speakers = s
	
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

	def initSim(self, myGraph, pos):
		self.tick = 0
		self.startTime = time.time()

		self.myGraph, self.pos = myGraph, pos

		self.grammar = self.myGraph.new_vertex_property("double")
		self.memory = self.myGraph.new_vertex_property("string")
		self.amplitude = self.myGraph.new_vertex_property("double")
		self.amplitudeMemory = self.myGraph.new_vertex_property("vector<double>")
		
		# initialize 
		for v in self.myGraph.vertices():
			self.grammar[v] = 0
			self.memory[v] = ""
			self.amplitude[v] = 0
			self.amplitudeMemory[v] = []
	
		# define an innovator
		self.grammar[self.myGraph.vertex(0)] = 1
		if self.waveAmplitude > 0: 
			self.amplitude[self.myGraph.vertex(0)] = self.waveAmplitude
		
		# color property
		self.colors = self.myGraph.new_vertex_property("vector<double>")
		for v in self.myGraph.vertices():
			self.colors[v] = self.calculateColor(self.grammar[v])
		
		print("simulation initiated.")

	def calculateColor(self, grammarValue):
		red = 1 - grammarValue
		green = 0.5 * grammarValue # forest green
		blue = 0
		alpha = 1
		return [red, green, blue, alpha]

	def stepSim(self):
		vertices = list(self.myGraph.vertices())
		shuffle(vertices)
		sumGValues = 0
		for thisVertex in vertices:
			#pick a neighbor
			neighbors = list(thisVertex.out_neighbours())
			if len(neighbors) > 0:
				neighbor = neighbors[randint(0, len(neighbors))]  # choose a random neighbour
			self.communicate(thisVertex, neighbor)

			# update colors
			self.colors[thisVertex] = self.calculateColor(self.grammar[thisVertex])
			sumGValues += self.grammar[thisVertex]
			
			# random chance to let agent die of old age (reset to defaults)
			#~ if (randint(0, 2000) == 0):
				#~ print ("an agent died", thisVertex)
				#~ self.grammar[thisVertex] = 0 # how should we initialize it?
				#~ self.memory[thisVertex] = ""
				#~ self.colors[thisVertex] = self.calculateColor(self.grammar[thisVertex])


		# save indexed values for later export (e.g. for plotting in R)
		sumAgents = self.myGraph.num_vertices()
		alpha_y = 100 / sumAgents * sumGValues
		beta_y = 100 / sumAgents * (sumAgents - sumGValues)
		self.logValues.append([self.tick, alpha_y, beta_y])
		
		self.tick += 1

	def communicate(self, agent, neighbor):
		utteranceAgent = self.produceUtterance(agent)
		utteranceNeighbor = self.produceUtterance(neighbor)
		
		if self.waveAmplitude > 0:
			self.updateAmplitude("α", utteranceAgent, agent, neighbor)
			self.updateAmplitude("α", utteranceNeighbor, neighbor, agent)
		
		oldGrammar = self.grammar[agent]
		oldMemory = self.memory[agent]

		#store in memory
		self.memory[agent] = self.truncateMemory(utteranceNeighbor + self.memory[agent])
		self.memory[neighbor] = self.truncateMemory(utteranceAgent + self.memory[neighbor])

		# calculate new grammar values
		agentGrammarNew = self.grammar[agent] + self.lambdaValue * (self.countARatio(self.memory[agent]) - self.grammar[agent])
		neighborGrammarNew = self.grammar[neighbor] + self.lambdaValue * (self.countARatio(self.memory[neighbor]) - self.grammar[neighbor])

		agentGrammarNew = round(agentGrammarNew, 10)
		neighborGrammarNew = round(neighborGrammarNew, 10)
		
		if self.discreteProduction:
			self.grammar[agent] = 0 if (agentGrammarNew <= 0.5) else 1
			self.grammar[neighbor] = 0 if (neighborGrammarNew <= 0.5) else 1
		else:
			self.grammar[agent] = agentGrammarNew
			self.grammar[neighbor] = neighborGrammarNew

	def produceUtterance(self, agent):
		u = ""
		for i in range(self.utteranceLength):
			myRand = random()
			bias = self.alphaBias
			if self.waveAmplitude > 0: bias = self.amplitude[agent] # if we are operating in the wave scenario, use the wave amplitude instead of the global bias
			if (myRand <= (self.grammar[agent] + bias)): u += "α" # apply own amplitude as bias
			else: u += "β"
		return u

	def countARatio(self, memory):
		if len(memory) == 0: return 0
		return memory.count('α')/len(memory)

	def truncateMemory(self, memory):
		return memory[:self.memorySize]

	def updateAmplitude(self, signal, utterance, agent, neighbor):
		if signal in utterance:
			amp = self.amplitude[agent] * 0.9 # when we pass it on, we reduce the amplitude by 10%
			if amp > 0.01: #ignore very small amplitudes
				self.amplitudeMemory[neighbor].append(amp) 
				m = self.amplitudeMemory[neighbor]
				self.amplitude[neighbor] = sum(m)/float(len(m))

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
		
		# export the sums of the g values, in a CSV format to be processed by e.g. R
		datFileName = str(dirName + 'frequencies.dat')
		f = open(datFileName, 'w')
		f.write("Ticks,AlphaY,BetaY\n")
		for i in range(len(self.logValues)):
			a = self.logValues[i]
			f.write(str(a[0]) + "," + str(a[1]) + "," + str(a[2]) + "\n")
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
		amplitudeFileName = str(dirName + "amplitude.dat")
		f = open(amplitudeFileName, 'w')
		for v in self.myGraph.vertices():
			f.write(str(self.amplitude[v]) + "\n")
		f.close()




