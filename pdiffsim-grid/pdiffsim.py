#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com

"""
import sys, configparser, math, time #, numpy
try:
	from PyQt4 import QtGui, QtCore
except ImportError:
	"No Qt module found. GUI will not be available."
from simmanager import SimManager
	
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
			self.simManager.exportData()
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
				p = self.simManager.grammarMatrix[x][y]
				green = math.floor(128 * p); # green according to CSS color definition
				red = math.floor(255 * (1 - p))
				thisColor = QtGui.QColor(red, green, 0)
				qp.fillRect(x * 4, y * 4, 4, 4, thisColor)
				
				#~ sumGValues += p
	def closeEvent(self, e):
		self.simManager.exportData()
		print("exiting.")
		e.accept()


# instantiate things

def main():

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
	simManager.setUtteranceLength(config.getint('simulation', 'utteranceLength'))
	nogui = config.getboolean('simulation', 'nogui')
	interactive = config.getboolean('simulation', 'interactive')
	runs = config.getint('simulation', 'runs')
	simManager.initSim()
	
	if nogui:
		for i in range(runs):
			simManager.stepSim()
		simManager.exportData()
	else:
		app = QtGui.QApplication(sys.argv)
		w = SimWidget(simManager)
		if not interactive:
			w.startTimer(100, runs) # interval (in milliseconds), number of runs
		sys.exit(app.exec_())


if __name__ == '__main__':
	main()
