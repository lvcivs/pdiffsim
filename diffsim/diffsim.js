// diffsim.js
// author: luzius thöny <luzius@ling.su.se>

// UTIL: matrix function
function matrix(rows, cols, defaultValue) {
	var a = [];
	for (var i = 0; i < rows; i++) {
		a.push([]);
		a[i].push(new Array(cols));
		for(var j = 0; j < cols; j++) {
			a[i][j] = defaultValue;
		}
	}
	return a;
}

// UTIL: Event class, implements Observer Pattern
function Event(sender) {
	this.sender = sender;
	this.listeners = [];
}

Event.prototype = {
	attach : function(listener) {
		this.listeners.push(listener);
	},
	notify : function(args) {
		for (var index = 0; index < this.listeners.length; index++) {
			this.listeners[index](this.sender, args);
		}
	}
};



function SimManager() {
	this.myMatrix;
	this.width = 40;
	this.height = 40;

	this.interval;
	this.running = 0;
	this.tick = 0;

	this.initScenario = "random";

	this.lambda = 0.5; // how likely the agent is to change its behaviour; 0.2: slow change, 0.8: fast change, 0.5: default
	this.memorySize = 20; //10: very fast change, 100: very slow change
	this.alphaBias = 1; // fitness of alpha, bias towards alpha (if given a choice between alpha and beta)
	this.errorRate = 0;
	this.neighborRange = 1;

	this.logValues = new Array();
	
	this.guiEvent = new Event(this);
	this.simStepEvent = new Event(this);
}

SimManager.prototype = {

	setGridSize : function(i) {
		this.stopSim();
		this.tick = 0;
		document.getElementById("ticks").innerHTML = this.tick;
		document.getElementById("stepButton").disabled = true;
		document.getElementById("runStopButton").disabled = true;

		this.width = i;
		this.height = i;
		this.myMatrix = 0;
		
		document.getElementById("simCanvas").width = i * 4;
		document.getElementById("simCanvas").height = i * 4;
	},

	chooseInitScenario : function(s) {
		this.initScenario = s;
	},

	setLambda : function(i) {
		this.lambda = i;
		this.guiEvent.notify();
	},

	setAlphaBias : function(i) {
		this.alphaBias = i;
		this.guiEvent.notify();
	},

	setMemorySize : function(i) {
		this.memorySize = i;
		this.guiEvent.notify();

	},

	setNeighborRange : function(i) {
		this.neighborRange = i;
		this.guiEvent.notify();
	},

	setWeighting : function(s) {
		var myClassName = "";
		var myDisabled = true;
		if (s === "none") {
			this.alphaBias = 1;
			myClassName = "grayed";
			myDisabled = true;
		} else if (s === "weighted") {
			myClassName = "";
			myDisabled = false;
		}
		document.getElementById("alphaBiasSpan").className = myClassName;
		document.getElementById("alphaBiasSlider").disabled = myDisabled;
		document.getElementById("alphaBiasSliderOutput").className = myClassName;
	},

	setErrorRate : function(i) {
		this.errorRate = i;
		this.guiEvent.notify();
	},

	initSim : function() {
		var myCanvas = document.getElementById("simCanvas");
		var myContext = myCanvas.getContext("2d");
		
		// clear canvases
		var plotCanvas = document.getElementById("plotCanvas");
		var plotContext = plotCanvas.getContext("2d");
		myCanvas.width = myCanvas.width;
		plotCanvas.width = plotCanvas.width;

		// draw horizontal lines on plot canvas
		plotContext.fillStyle = "#ccc";
		plotContext.font = 'bold 8pt Arial'
		for (var i = 0; i < 5; i++) {
			plotContext.fillRect(0, i * 25, 800, 1);
			plotContext.fillText((100-(i * 25)).toString(), 10, 10 + i * 25);
		}

		this.tick = 0;
		this.logValues = new Array();
		document.getElementById("stepButton").disabled = false;
		document.getElementById("runStopButton").disabled = false;

		this.myMatrix = matrix(this.height, this.width, 0);
		
		// purely random
		if (this.initScenario === "random") {
			for (var x = 0; x < this.width; x++) {
				for (var y = 0; y < this.height; y++) {
					this.myMatrix[x][y] = [0.5 + (Math.random() - 0.5) / 2, ""]; // probability of saying α, agent's memory (as a string)
				}
			}
		}

		//island
		if (this.initScenario === "island") {
			for (var x = 0; x < this.width; x++) {
				for (var y = 0; y < this.height; y++) {
					this.myMatrix[x][y] = [0, ""];
					var blockwidth = 4;
					if (x > (this.width / 2) - (blockwidth / 2) && x < (this.width / 2) + (blockwidth / 2) && y > (this.height / 2) - (blockwidth / 2) && y < (this.height / 2) + (blockwidth / 2) ) {
						this.myMatrix[x][y] = [1, ""];
					}
					
				}
			}
		}

		//two fields
		if (this.initScenario === "two fields") {
			for (var x = 0; x < this.width; x++) {
				for (var y = 0; y < this.height; y++) {
					this.myMatrix[x][y] = [0, ""];
					var blockwidth = 4;
					if (x >= (this.width / 2) ) {
						this.myMatrix[x][y] = [1, ""];
					}
					
				}
			}
		}

		this.simStepEvent.notify();
	},

	runSim : function() { // run or stop
		if (!this.running) {
			this.interval = setInterval(function() {g_simManager.stepSim();}, 50);
			this.running = 1;
			document.getElementById("initButton").disabled = true;
			document.getElementById("stepButton").disabled = true;
		} else {
			this.stopSim();
		}
	},

	stopSim : function() {
		clearInterval(this.interval);
		this.running = 0;
		document.getElementById("initButton").disabled = false;
		document.getElementById("stepButton").disabled = false;

	},

	stepSim : function () {
		var neighbor = 0;
		this.tick++;

		for (var x = this.width-1; x >= 0; x-- ) { 
			for (var y = 0; y < this.height; y++) {
				var agentCoords = [x, y];
				var neighborCoords = this.selectNeighbor(agentCoords);
				this.communicate(agentCoords, neighborCoords); 
			}
		}
		
		// save indexed values for later export (e.g. for plotting in R)
		var sumGValues = 0;
		for (var x = 0; x < this.width; x++) {
			for (var y = 0; y < this.height; y++) {
				var p = this.myMatrix[x][y][0];
				sumGValues += p;
			}
		}
		var sumAgents = this.width * this.height;
		var alpha_y = 100 / sumAgents * sumGValues;
		var beta_y = 100 / sumAgents * (sumAgents - sumGValues);
		this.logValues.push([this.tick, alpha_y, beta_y]);

		this.simStepEvent.notify();
	},

// endless space (wrap neighbors over border)
//~ function borderCheck(xy) {
	//~ var x = xy[0];
	//~ var y = xy[1];
	//~ if (x < 0) x = g_width - 1;
	//~ if (y < 0) y = g_height - 1;
	//~ if (x == g_width) x = 0;
	//~ if (y == g_height) y = 0;
	//~ return [x, y];
//~ }

// finite space (borders are limits)
	borderCheck : function(xy) {
		var x = xy[0];
		var y = xy[1];
		if (x < 0) return false;
		if (y < 0) return false;
		if (x >= this.width) return false;
		if (y >= this.height) return false;
		return true;
	},

	isValidNeighbor : function(coords1, coords2) {
		if (! this.borderCheck(coords2)) return false;
		if (coords1[0] == coords2[0] && coords1[1] == coords2[1]) return false;
		return true;
	},

// alternative code to find neighbor, does not need to be direct neighbor but up to n positions away
// closer ones should be more likely to be chosen
	selectNeighbor : function(thisAgent) {
		var x_offset;
		var y_offset;
		var thisNeighbor;

		// retry if coords are out of bounds
		do { 
			x_offset = this.findNeighborOffset(this.neighborRange);
			y_offset = this.findNeighborOffset(this.neighborRange);
			thisNeighbor = [thisAgent[0] + x_offset, thisAgent[1] + y_offset];
		} 
		while (! this.isValidNeighbor(thisAgent, thisNeighbor));
		return thisNeighbor;
	},

// calculate by how much this neighbor's coordinate shall be offset
// using an exponential function, so that closer ones are more likely to be selected
//  y = r^2*7
// 50% chance of negative value
	findNeighborOffset : function(max) {
		var v = Math.round(Math.pow(Math.random(), 2) * max) ;
		if (Math.floor(Math.random() * 2) === 1) v = v * -1;
		return v;
	},

	communicate : function(agentCoords, neighborCoords) {
		var utteranceAgent = this.produceUtterance(agentCoords);
		var utteranceNeighbor = this.produceUtterance(neighborCoords);
		
		var xAgent = agentCoords[0];
		var yAgent = agentCoords[1];
		
		var xNeighbor = neighborCoords[0];
		var yNeighbor = neighborCoords[1];
		
		//store in memory
		var agentMemory = this.truncateMemory(this.applyError(utteranceNeighbor) + this.myMatrix[xAgent][yAgent][1]);
		var neighborMemory = this.truncateMemory(this.applyError(utteranceAgent) + this.myMatrix[xNeighbor][yNeighbor][1]);
		
		// adapt grammar
		var agentGrammar = this.myMatrix[xAgent][yAgent][0];
		var neighborGrammar = this.myMatrix[xNeighbor][yNeighbor][0];
		
		var agentGrammarNew = agentGrammar + this.lambda * (this.countARatio(agentMemory) - agentGrammar);
		var neighborGrammarNew = neighborGrammar + this.lambda * (this.countARatio(neighborMemory) - neighborGrammar);

		this.myMatrix[xAgent][yAgent] = [agentGrammarNew, agentMemory];
		this.myMatrix[xNeighbor][yNeighbor] = [neighborGrammarNew, neighborMemory];

	},

	produceUtterance : function(agentCoords) {
		var x = agentCoords[0];
		var y = agentCoords[1];
		var u = "";
		for (var i = 0; i < 10; i++) {
			var myRand = Math.random();
			var agentGrammar = this.myMatrix[x][y][0];
			if (myRand <= agentGrammar * this.alphaBias) u += "α"; // bias is implemented by multiplication
			else u += "β"; 
		}
		return u;
	},

	countARatio : function(memory) {
		var counter = 0;
		for (var i = 0; i < memory.length; i++) {
			if (memory.charAt(i) === "α") counter++;
		}
		return counter/memory.length;
		
	},

	truncateMemory : function(memory) {
		if (memory.length > this.memorySize) memory = memory.substring(0, this.memorySize); 
		return memory;
	},

	applyError : function(s) { // (potentially) introduce misunderstandings between speaker and hearer
		var result = "";
		for (var i = 0; i < s.length; i++) {
			var thisChar = s[i];
			var thisResultChar = thisChar;
			if (Math.random() < this.errorRate) {
				//switch them around
				if (thisChar === "β") thisResultChar = "α";
				else thisResultChar = "β";
			}
			result += thisResultChar;
		}
		return result;
	},
	
	// export the plot values, in a CSV format to be processed by e.g. R
	exportLogValues : function() {
		var myWindow = window.open("", "Export Data");
		myWindow.document.writeln("Ticks,AlphaY,BetaY<br>");
		for (var i = 0; i < this.logValues.length; i++) {
			var a = this.logValues[i];
			myWindow.document.writeln(a[0] + "," + a[1] + "," + a[2] + "<br>");
		}
	}

};


function SimView(simManager) {
	this.simManager = simManager;
	var _this = this;

	this.simManager.guiEvent.attach(function() {_this.updateGUI()});
	this.simManager.simStepEvent.attach(function() {_this.drawToCanvas()});
}

SimView.prototype = {
	updateGUI : function() {
		document.querySelector('#ticks').innerHTML = this.simManager.tick;
		document.querySelector('#memorySizeSliderOutput').innerHTML = this.simManager.memorySize;
		document.querySelector('#lambdaSliderOutput').innerHTML = this.simManager.lambda;
		document.querySelector('#neighborRangeSliderOutput').innerHTML = this.simManager.neighborRange;
		document.querySelector('#alphaBiasSliderOutput').innerHTML = this.simManager.alphaBias;
		document.querySelector('#errorRateSliderOutput').innerHTML = this.simManager.errorRate;
	},
	
	drawToCanvas : function() {
		var myCanvas = document.getElementById("simCanvas");
		var myContext = myCanvas.getContext("2d");
		
		var sumGValues = 0;

		//draw simulation on grid
		for (var x = 0; x < this.simManager.width; x++) {
			for (var y = 0; y < this.simManager.height; y++) {
				var p = this.simManager.myMatrix[x][y][0];
				var green = Math.floor(128 * p); // green according to CSS color definition
				var red = Math.floor(255 * (1 - p));
				var color = "rgb(" + red + "," + green + ", 0)";
				myContext.fillStyle = color;
				myContext.fillRect(x * 4, y * 4, 4, 4);
				
				sumGValues += p;
			}
		}
				
		// draw plot
		var plotCanvas = document.getElementById("plotCanvas");
		var plotContext = plotCanvas.getContext("2d");
		var sumAgents = this.simManager.width * this.simManager.height;
		var alpha_y = 100 / sumAgents * sumGValues;
		var beta_y = 100 / sumAgents * (sumAgents - sumGValues);
		
		plotContext.fillStyle = "green";
		plotContext.fillRect(this.simManager.tick + 5, 100 - alpha_y, 2, 2);
		plotContext.fillStyle = "red";
		plotContext.fillRect(this.simManager.tick + 5, 100 - beta_y, 2, 2);
	}
	
}

// global variables
var g_simManager = 0;
var g_simView = 0;

// instantiation
window.onload = function() {
	g_simManager = new SimManager();
	g_simView = new SimView(g_simManager);

	// attach GUI event listeners
	document.querySelector("#memorySizeSlider").addEventListener('change', function() {
		g_simManager.setMemorySize(this.value);
	}, false);
	document.querySelector("#lambdaSlider").addEventListener('change', function() {
		g_simManager.setLambda(this.value);
	}, false);
	document.querySelector("#neighborRangeSlider").addEventListener('change', function() {
		g_simManager.setNeighborRange(this.value);
	}, false);
	document.querySelector("#alphaBiasSlider").addEventListener('change', function() {
		g_simManager.setAlphaBias(this.value);
	}, false);
	document.querySelector("#errorRateSlider").addEventListener('change', function() {
		g_simManager.setErrorRate(this.value);
	}, false);
	

	document.querySelector("#gridSizeRadio20").addEventListener('click', function() {
		g_simManager.setGridSize(20);
	}, false);
	document.querySelector("#gridSizeRadio40").addEventListener('click', function() {
		g_simManager.setGridSize(40);
	}, false);
	document.querySelector("#gridSizeRadio80").addEventListener('click', function() {
		g_simManager.setGridSize(80);
	}, false);
		
	document.querySelector("#initScenario").addEventListener('change',  function() {
		g_simManager.chooseInitScenario(this[this.selectedIndex].value)
	}, false);
	
	document.querySelector("#weightingoff").addEventListener('click', function() {
		g_simManager.setWeighting("none");
	}, false);
	document.querySelector("#weightingon").addEventListener('click', function() {
		g_simManager.setWeighting("weighted");
	}, false);
		
	document.querySelector("#initButton").addEventListener('click', function() {
		g_simManager.initSim();
	}, false);
	document.querySelector("#stepButton").addEventListener('click', function() {
		g_simManager.stepSim();
	}, false);
	document.querySelector("#runStopButton").addEventListener('click', function() {
		g_simManager.runSim();
	}, false);
	document.querySelector("#exportLink").addEventListener('click', function() {
		g_simManager.exportLogValues();
	}, false);

}

