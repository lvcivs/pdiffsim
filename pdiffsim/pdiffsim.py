#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com

"""

import sys, random, math, configparser, time, threading #, numpy
try:
	from PyQt4 import QtGui, QtCore
except ImportError:
	"No Qt module found. GUI will not be available."
	
class SimWidget(QtGui.QWidget):
	
	def __init__(self, simManager):
		super(SimWidget, self).__init__()
		self.initUI()

		self.simManager = simManager
		
		# make the GUI update itself whenever the simulation is advanced
		simManager.visUpdateEvent.attach(self.update)
		
	def startTimer(self, milliseconds, runs):
		# this timer allows to run the simulation automatically in a loop for n runs
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.incrementTimer)
		self.timer.start(milliseconds)
		self.timerCount = 0
		self.timerRuns = runs

	def incrementTimer(self):
		self.timerCount += 1 
		if self.timerCount > self.timerRuns:
			self.timer.stop()
			self.simManager.exportLogValues()
		else:
			self.simManager.stepSim()


	def initUI(self):      
		#~ self.setGeometry(300, 300, 280, 170)
		self.setGeometry(1800, 300, 600, 600)
		self.setWindowTitle('DiffSim')
		self.show()

	def paintEvent(self, e=None):
		qp = QtGui.QPainter()
		qp.begin(self)
		self.drawSim(qp)
		qp.end()

	def keyPressEvent(self, e):
		if e.key() == QtCore.Qt.Key_Right or e.key() == QtCore.Qt.Key_Down:
			self.simManager.stepSim()

	def drawSim(self, qp):
		# draw simulation on grid
		for x in range(self.simManager.width):
			for y in range(self.simManager.height):
				p = self.simManager.myMatrix[x][y][0]
				green = math.floor(128 * p); # green according to CSS color definition
				red = math.floor(255 * (1 - p))
				thisColor = QtGui.QColor(red, green, 0)
				qp.fillRect(x * 4, y * 4, 4, 4, thisColor)
				
				#~ sumGValues += p
	def closeEvent(self, e):
		self.simManager.exportLogValues()
		print("exiting.")
		e.accept()
"""
"""


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

		self.myMatrix = []
		self.width = 80
		self.height = 80

		self.running = 0
		self.tick = 0

		self.initScenario = "random"

		self.lambdaValue = 0.5 # how likely the agent is to change its behaviour; 0.2: slow change, 0.8: fast change, 0.5: default
		self.memorySize = 20 #10: very fast change, 100: very slow change
		self.alphaBias = 1 # fitness of alpha, bias towards alpha (if given a choice between alpha and beta)
		self.errorRate = 0
		self.neighborRange = 1

		self.logFileName = ""
		self.logValues = []
		
		self.visUpdateEvent = Event()

	def setLogFileName(self, s):
		self.logFileName = s

	def setGridSize(self, i):
		#~ self.stopSim()
		self.tick = 0

		self.width = i
		self.height = i
		self.myMatrix = 0
	
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

	def initSim(self):
		self.tick = 0
		self.logValues = []

		self.myMatrix = [[0 for x in range(self.width)] for x in range(self.height)] 
		
		# purely random
		if (self.initScenario == "random"):
			for x in range(self.width):
				for y in range(self.height):
					self.myMatrix[x][y] = [0.5 + (random.random() - 0.5) / 2, ""]; # probability of saying α, agent's memory (as a string)

		#island
		if (self.initScenario == "island"):
			for x in range(self.width):
				for y in range(self.height):
					self.myMatrix[x][y] = [0, ""]
					blockwidth = 4
					if (x > (self.width / 2) - (blockwidth / 2) and x < (self.width / 2) + (blockwidth / 2) and y > (self.height / 2) - (blockwidth / 2) and y < (self.height / 2) + (blockwidth / 2) ):
						self.myMatrix[x][y] = [1, ""]

		#two fields
		if (self.initScenario == "two fields"):
			for x in range(self.width):
				for y in range(self.height):
					self.myMatrix[x][y] = [0, ""]
					blockwidth = 4
					if (x >= (width / 2) ):
						self.myMatrix[x][y] = [1, ""]

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
				p = self.myMatrix[x][y][0]
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
		agentMemory = self.truncateMemory(self.applyError(utteranceNeighbor) + self.myMatrix[xAgent][yAgent][1])
		neighborMemory = self.truncateMemory(self.applyError(utteranceAgent) + self.myMatrix[xNeighbor][yNeighbor][1])
		
		# adapt grammar
		agentGrammar = self.myMatrix[xAgent][yAgent][0]
		neighborGrammar = self.myMatrix[xNeighbor][yNeighbor][0]
		
		agentGrammarNew = agentGrammar + self.lambdaValue * (self.countARatio(agentMemory) - agentGrammar)
		neighborGrammarNew = neighborGrammar + self.lambdaValue * (self.countARatio(neighborMemory) - neighborGrammar)

		self.myMatrix[xAgent][yAgent] = [agentGrammarNew, agentMemory]
		self.myMatrix[xNeighbor][yNeighbor] = [neighborGrammarNew, neighborMemory]

	
	def produceUtterance(self, agentCoords):
		x = agentCoords[0]
		y = agentCoords[1]
		u = ""
		for i in range(10):
			myRand = random.random()
			agentGrammar = self.myMatrix[x][y][0]
			if (myRand <= agentGrammar * self.alphaBias): u += "α" # bias is implemented by multiplication
			else: u += "β"
		#~ print("says: " + u)

		return u

	def countARatio(self, memory):
		counter = 0
		for i in range (len(memory)):
			if (memory[i] == "α"): counter += 1
		return counter/len(memory)

	def truncateMemory(self, memory):
		if (len(memory) > self.memorySize): memory = memory[0:self.memorySize]
		return memory


	def applyError(self, s): # (potentially) introduce misunderstandings between speaker and hearer
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
	
	# export the plot values, in a CSV format to be processed by e.g. R
	def exportLogValues(self):
		print("writing to log file: " + self.logFileName)
		f = open(self.logFileName, 'w')
		f.write("Ticks,AlphaY,BetaY\n")
		for i in range(len(self.logValues)):
			a = self.logValues[i]
			f.write(str(a[0]) + "," + str(a[1]) + "," + str(a[2]) + "\n")
		f.close()



# instantiate things

def main():
	startTime = time.time()
	
	if len(sys.argv) == 1 : 
		print("No config file specified.\nUsage: pdiffsym.py [Config File]")
		return

	config = configparser.ConfigParser()
	config.read(sys.argv[1])

	simManager = SimManager()
	simManager.setLogFileName(str(sys.argv[1])[:-4] + ".log")
	simManager.setGridSize(config.getint('simulation', 'gridSize'))
	simManager.setInitScenario(config.get('simulation', 'initScenario'))
	simManager.setLambdaValue(config.getfloat('simulation', 'lambdaValue'))
	simManager.setMemorySize(config.getint('simulation', 'memorySize'))
	simManager.setAlphaBias(config.getfloat('simulation', 'alphaBias'))
	simManager.setErrorRate(config.getfloat('simulation', 'errorRate'))
	simManager.setNeighborRange(config.getint('simulation', 'neighborRange'))
	nogui = config.getboolean('simulation', 'nogui')
	interactive = config.getboolean('simulation', 'interactive')
	runs = config.getint('simulation', 'runs')
	simManager.initSim()
	
	if nogui:
		for i in range(runs):
			simManager.stepSim()
		simManager.exportLogValues()
		print("--- elapsed time: %s seconds ---" % str(time.time() - startTime)) # note that this will depend on other work load on the machine, as well
	else:
		app = QtGui.QApplication(sys.argv)
		w = SimWidget(simManager)
		if not interactive:
			w.startTimer(100, runs) # interval (in milliseconds), number of runs
		sys.exit(app.exec_())


if __name__ == '__main__':
	main()
