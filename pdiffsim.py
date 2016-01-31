#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
author: Luzius Thöny
lucius.antonius@gmail.com
2016

"""

import sys, os, os.path, math
from numpy.random import *
from distutils.dir_util import mkpath
import configparser
import scipy.misc as sm
import numpy

from simmanager import SimManager


if len(sys.argv) == 1 : 
	print("No config file specified.\nUsage: pdiffsym_gt.py [Config File]")
	sys.exit(0)

simManager = SimManager()
outputDir = str(sys.argv[1])[:-4] + ".log" + "/"

# optionally write results to subfolder (useful when we start the simulation repeatedly from a bash script)
if len(sys.argv) > 2:
	subfolderNo = sys.argv[2]
	if subfolderNo: outputDir = outputDir + subfolderNo + "/"

simManager.setOutputDir(outputDir)


# Read config file
config = configparser.ConfigParser()
config.read(sys.argv[1])

gridSize = config.getint('simulation', 'gridSize')
simManager.setGridSize(gridSize)
simManager.setLambdaValue(config.getfloat('simulation', 'lambdaValue'))
simManager.setMemorySize(config.getint('simulation', 'memorySize'))
simManager.setAlphaBias(config.getfloat('simulation', 'alphaBias'))
simManager.setErrorRate(config.getfloat('simulation', 'errorRate'))
simManager.setUtteranceLength(config.getint('simulation', 'utteranceLength'))
simManager.setDiscreteProduction(config.getboolean('simulation', 'discreteProduction'))
simManager.setWaveAmplitude(config.getfloat('simulation', 'waveAmplitude'))
snapshotInterval = config.getint('simulation', 'snapshotInterval')
timesteps = config.getint('simulation', 'timesteps')
simManager.setTimesteps(timesteps)
simManager.initSim()


mkpath("./" + outputDir)

# main simulation loop
for i in range(timesteps):
	simManager.stepSim()
	if (simManager.tick % snapshotInterval == 0):
		# save image to disk
		imgname = outputDir + 'frame' + str(simManager.tick).zfill(4) + '.png'
		arr = numpy.array(simManager.colors.matrix)
		#~ for x in numpy.nditer(arr):
			#~ x = x * 255
		sm.imsave(imgname, arr)

simManager.exportData()
print("done running the simulation. exported data.")


