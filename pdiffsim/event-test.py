#!/usr/bin/python
# -*- coding: utf-8 -*-

class Event:
	def __init__(self):
		self.listeners = []
	def attach(self, listener):
		self.listeners.append(listener);
	def fire(self):
		for listener in self.listeners:
			listener()

class Test:
	def printOut(self):
		print("output")

	def printOut2(self):
		print("output2")

t = Test()
e1 = Event()
e1.attach(t.printOut2)
e2 = Event()
e2.attach(t.printOut)
e2.attach(t.printOut2)
e1.fire()
e2.fire()
