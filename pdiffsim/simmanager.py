#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com

"""

import random, math, time, scipy, numpy
import scipy.misc as scipymisc
from distutils.dir_util import mkpath

# UTIL
class Event:
	def __init__(self):
		self.listeners = []
	def attach(self, listener):
		self.listeners.append(listener);
	def fire(self):
		for listener in self.listeners:
			listener()
			#~ print("event fired: " + str(listener))


class SimManager:
	
	def __init__(self):

		self.grammarMatrix = []
		self.memoryMatrix = []
		self.width = 0
		self.height = 0

		self.running = 0
		self.tick = 0

		self.initScenario = ""

		self.lambdaValue = 0 # how likely the agent is to change its behaviour; 0.2: slow change, 0.8: fast change, 0.5: default
		self.memorySize = 0 #10: very fast change, 100: very slow change
		self.alphaBias = 0 # fitness of alpha, bias towards alpha (if given a choice between alpha and beta)
		self.errorRate = 0
		self.neighborRange = 0
		self.utteranceLength = 0

		self.logFileName = ""
		self.logValues = []
		
		self.startTime = 0
		
		self.visUpdateEvent = Event()

	def setLogFileName(self, s):
		self.logFileName = s
		

	def setGridSize(self, i):
		#~ self.stopSim()
		self.tick = 0

		self.width, self.height = i, i
	
	def setInitScenario(self, s):
		self.initScenario = s
	
	def setLambdaValue(self, i):
		self.lambdaValue = i
		self.visUpdateEvent.fire()
	
	def setAlphaBias(self, i):
		self.alphaBias = i
		self.visUpdateEvent.fire()
	
	def setMemorySize(self, i):
		self.memorySize = i
		self.visUpdateEvent.fire()

	def setNeighborRange(self, i):
		self.neighborRange = i
		self.visUpdateEvent.fire()
	
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
		self.visUpdateEvent.fire()
		
	def setUtteranceLength(self, i):
		self.utteranceLength = i
		self.visUpdateEvent.fire()

	def initSim(self):
		self.tick = 0
		self.logValues = []

		self.grammarMatrix = [[0 for x in range(self.width)] for x in range(self.height)] 
		self.memoryMatrix = [["" for x in range(self.width)] for x in range(self.height)] 
		# numpy arrays; turns out to be slower, though
		#~ self.grammarMatrix = scipy.empty((self.width, self.height))
		#~ self.memoryMatrix = numpy.array([['' for x in range(self.width)] for x in range(self.height)], dtype="U10") # data type: Unicode, string length 10
		
		# purely random
		if (self.initScenario == "random"):
			for x in range(self.width):
				for y in range(self.height):
					self.grammarMatrix[x][y] = 0.5 + (random.random() - 0.5) / 2 # probability of saying α, agent's memory (as a string)

		#island
		if (self.initScenario == "island"):
			for x in range(self.width):
				for y in range(self.height):
					self.grammarMatrix[x][y] = 0
					blockwidth = 4
					if (x > (self.width / 2) - (blockwidth / 2) and x < (self.width / 2) + (blockwidth / 2) and y > (self.height / 2) - (blockwidth / 2) and y < (self.height / 2) + (blockwidth / 2) ):
						self.grammarMatrix[x][y] = 1

		#two fields
		if (self.initScenario == "two fields"):
			for x in range(self.width):
				for y in range(self.height):
					self.grammarMatrix[x][y] = 0
					blockwidth = 4
					if (x >= (self.width / 2) ):
						self.grammarMatrix[x][y] = 1

		self.startTime = time.time()

		self.visUpdateEvent.fire()
	

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
		self.neighbor = 0
		self.tick += 1

		for x in reversed(range(self.width)):
			for y in range(self.height):
				agentCoords = [x, y]
				neighborCoords = self.selectNeighbor(agentCoords)
				self.communicate(agentCoords, neighborCoords)
		
		# save indexed values for later export (e.g. for plotting in R)
		sumGValues = 0
		for x in range(self.width):
			for y in range(self.height):
				p = self.grammarMatrix[x][y]
				sumGValues += p

		sumAgents = self.width * self.height
		alpha_y = 100 / sumAgents * sumGValues
		beta_y = 100 / sumAgents * (sumAgents - sumGValues)
		self.logValues.append([self.tick, alpha_y, beta_y])

		self.visUpdateEvent.fire()
	

# endless space (wrap neighbors over border)
#~ def borderCheck(xy):
	#~ var x = xy[0]
	#~ var y = xy[1]
	#~ if (x < 0) x = g_width - 1
	#~ if (y < 0) y = g_height - 1
	#~ if (x == g_width) x = 0
	#~ if (y == g_height) y = 0
	#~ return [x, y]
#~

# finite space (borders are limits)
	def borderCheck(self, xy):
		x = xy[0]
		y = xy[1]
		if (x < 0) or (y < 0): return False
		if (x >= self.width) or (y >= self.height): return False
		return True

	def isValidNeighbor(self, coords1, coords2):
		if not self.borderCheck(coords2): return False
		if (coords1[0] == coords2[0] and coords1[1] == coords2[1]): return False
		return True
	

# alternative code to find neighbor, does not need to be direct neighbor but up to n positions away
# closer ones should be more likely to be chosen
	def selectNeighbor(self, thisAgent):
		x_offset = 0
		y_offset = 0
		thisNeighbor = 0

		# retry if coords are out of bounds
		while True:
			x_offset = self.findNeighborOffset(self.neighborRange)
			y_offset = self.findNeighborOffset(self.neighborRange)
			thisNeighbor = [thisAgent[0] + x_offset, thisAgent[1] + y_offset]
			if self.isValidNeighbor(thisAgent, thisNeighbor):
				return thisNeighbor


	# calculate by how much this neighbor's coordinate shall be offset
	# using an exponential function, so that closer ones are more likely to be selected
	#  y = r^2*7
	# 50% chance of negative value
	def findNeighborOffset(self, maxValue):
		v = int(round(math.pow(random.random(), 2) * maxValue, 0))
		if (math.floor(random.random() * 2) == 1): v = v * -1
		return v
	

	def communicate(self, agentCoords, neighborCoords):
		utteranceAgent = self.produceUtterance(agentCoords)
		utteranceNeighbor = self.produceUtterance(neighborCoords)
		
		xAgent = agentCoords[0]
		yAgent = agentCoords[1]
		
		xNeighbor = neighborCoords[0]
		yNeighbor = neighborCoords[1]
		
		#store in memory
		agentMemory = self.truncateMemory(self.applyError(utteranceNeighbor) + self.memoryMatrix[xAgent][yAgent])
		neighborMemory = self.truncateMemory(self.applyError(utteranceAgent) + self.memoryMatrix[xNeighbor][yNeighbor])
		
		# adapt grammar
		agentGrammar = self.grammarMatrix[xAgent][yAgent]
		neighborGrammar = self.grammarMatrix[xNeighbor][yNeighbor]
		
		agentGrammarNew = agentGrammar + self.lambdaValue * (self.countARatio(agentMemory) - agentGrammar)
		neighborGrammarNew = neighborGrammar + self.lambdaValue * (self.countARatio(neighborMemory) - neighborGrammar)

		agentGrammarNew = round(agentGrammarNew, 10)
		neighborGrammarNew = round(neighborGrammarNew, 10)
		
		self.grammarMatrix[xAgent][yAgent] = agentGrammarNew
		self.grammarMatrix[xNeighbor][yNeighbor] = neighborGrammarNew
		self.memoryMatrix[xAgent][yAgent] = agentMemory
		self.memoryMatrix[xNeighbor][yNeighbor] = neighborMemory

	
	def produceUtterance(self, agentCoords):
		x = agentCoords[0]
		y = agentCoords[1]
		u = ""
		agentGrammar = self.grammarMatrix[x][y]
		for i in range(self.utteranceLength):
			myRand = random.random()
			if (myRand <= agentGrammar * self.alphaBias): u += "α" # bias is implemented by multiplication
			else: u += "β"
		return u

	def countARatio(self, memory):
		return memory.count('α')/len(memory)

	def truncateMemory(self, memory):
		return memory[:self.memorySize]


	def applyError(self, s): # (potentially) introduce misunderstandings between speaker and hearer
		if self.errorRate == 0: return s
		result = ""
		for i in range(len(s)):
			thisChar = s[i]
			thisResultChar = thisChar
			if (random.random() < self.errorRate):
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
		f.write("elapsed time: %s seconds" % str(time.time() - self.startTime)) # note that this will depend on other work load on the machine, as well
		f.close()
		
		# export the plot values, in a CSV format to be processed by e.g. R
		datFileName = str(dirName + self.logFileName)[:-4] + '.dat'
		f = open(datFileName, 'w')
		f.write("Ticks,AlphaY,BetaY\n")
		for i in range(len(self.logValues)):
			a = self.logValues[i]
			f.write(str(a[0]) + "," + str(a[1]) + "," + str(a[2]) + "\n")
		f.close()
		
		#~ numpy.set_printoptions(threshold=numpy.inf)
		grammarFileName = str(dirName + "grammar.dat")
		f = open(grammarFileName, 'w')
		f.write(str(self.grammarMatrix))
		f.close()
		memoryFileName = str(dirName + "memory.dat")
		f = open(memoryFileName, 'w')
		f.write(str(self.memoryMatrix))
		f.close()
		
		# prepare image matrix, save to file
		imageMatrix = numpy.zeros((self.width*4, self.height*4, 3), dtype=numpy.uint8)
		for x in range(self.width):
			for y in range(self.height):
				p = self.grammarMatrix[x][y]
				green = math.floor(128 * p); # green according to CSS color definition
				red = math.floor(255 * (1 - p))
				thisColor = [red, green, 0]
				imgX = x * 4
				imgY = y * 4
				for i in range(4): imageMatrix[imgX+i][imgY:imgY+4] = thisColor
		img = scipymisc.toimage(imageMatrix)
		imgFileName = str(dirName + "final.png")
		scipymisc.imsave(imgFileName, img)



