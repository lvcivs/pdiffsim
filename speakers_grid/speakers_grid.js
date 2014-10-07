var g_myMatrix;
var g_width = 40;
var g_height = 40;

var g_interval;
var g_running = 0;
var g_tick = 0;

var g_initScenario = "random";

var g_lambda = 0.5; // how likely the agent is to change its behaviour; 0.2: slow change, 0.8: fast change, 0.5: default
var g_memoryLimit = 20; //10: very fast change, 100: very slow change
var g_alphaBias = 1; // fitness of alpha, bias towards alpha (if given a choice between alpha and beta)
var g_errorRate = 0;
var g_neighborRange = 1;

// matrix function from stackoverflow
function matrix(rows, cols, defaultValue) {
	var arr = [];

	for (var i = 0; i < rows; i++){
		arr.push([]);
		arr[i].push(new Array(cols));
		for(var j=0; j < cols; j++){
			arr[i][j] = defaultValue;
		}
	}
	return arr;
}


function setGridSize(i) {
	
	stopSim();
	g_tick = 0;
	document.getElementById('ticks').innerHTML = g_tick;
	document.getElementById("stepButton").disabled = true;
	document.getElementById("runStopButton").disabled = true;

	g_width = i;
	g_height = i;
	g_myMatrix = 0;
	
	document.getElementById("simCanvas").width = i * 4;
	document.getElementById("simCanvas").height = i * 4;

}


function chooseInitScenario(s) {
	
	//~ console.log("s=" + s);
	g_initScenario = s;
	
}

function setMemory(i) {
	g_memoryLimit = i;
}

function setLambda(i) {
	g_lambda = i;
}

function setAlphaBias(i) {
	g_alphaBias = i;
}

function setMemory(i) {
	g_memoryLimit = i;
}

function setLambda(i) {
	g_lambda = i;
}

function setAlphaBias(i) {
	g_alphaBias = i;
}

function setNeighborRange(i) {
	g_neighborRange = i;
}


function setWeighting(s) {
	var myClassName = "";
	var myDisabled = true;
	if (s === "none") {
		g_alphaBias = 1;
		myClassName = "grayed";
		myDisabled = true;
	} else if (s === "weighted") {
		myClassName = "";
		myDisabled = false;
	}
	document.getElementById("alphaBiasSpan").className = myClassName;
	document.getElementById("alphaBiasSlider").disabled = myDisabled;
}

function setErrorRate(i) {
	g_errorRate = i;
}
function initSim() {
	var myCanvas = document.getElementById("simCanvas");
	var myContext = myCanvas.getContext("2d");
	
	// clear canvases
	var plotCanvas = document.getElementById("plotCanvas");
	var plotContext = plotCanvas.getContext("2d");
	myCanvas.width = myCanvas.width;
	plotCanvas.width = plotCanvas.width;

	// draw lines on plot canvas
	plotContext.fillStyle = "#ccc";
	plotContext.font = 'bold 8pt Arial'
	for (var i = 0; i < 5; i++) {
		plotContext.fillRect(0, i*25, 800, 1);
		plotContext.fillText((100-(i*25)).toString(), 10, 10+i*25);
	}

	
	g_tick = 0;
	document.getElementById("stepButton").disabled = false;
	document.getElementById("runStopButton").disabled = false;

	g_myMatrix = matrix(g_height, g_width, 0);// initial probability, initial memory
	
	// purely random
	if (g_initScenario === "random") {
		for (var x = 0; x < g_width; x++) {
			for (var y = 0; y < g_height; y++) {
				g_myMatrix[x][y] = [0.5 + (Math.random() - 0.5)/2, ""]; // probability of saying α
			}
		}
	}

	//island
	if (g_initScenario === "island") {
		for (var x = 0; x < g_width; x++) {
			for (var y = 0; y < g_height; y++) {
				g_myMatrix[x][y] = [0, ""]; // probability of saying α
				var blockwidth = 4;
				if (x > (g_width / 2) - (blockwidth / 2) && x < (g_width / 2) + (blockwidth / 2) && y > (g_height / 2) - (blockwidth / 2) && y < (g_height / 2) + (blockwidth / 2) ) {
					g_myMatrix[x][y] = [1, ""];
				}
				
			}
		}
	}

	//two fields
	if (g_initScenario === "two fields") {
		for (var x = 0; x < g_width; x++) {
			for (var y = 0; y < g_height; y++) {
				g_myMatrix[x][y] = [0, ""]; // probability of saying α, agent's memory (as a string)
				var blockwidth = 4;
				if (x > (g_width / 2) ) {
					g_myMatrix[x][y] = [1, ""];
				}
				
			}
		}
	}


	drawToCanvas();
}

function runSim() { // run or stop
	if (!g_running) {
		g_interval = setInterval(stepSim,50);
		g_running = 1;
		document.getElementById("initButton").disabled = true;
		document.getElementById("stepButton").disabled = true;
	} else {
		stopSim();
	}
}

function stopSim() {
	clearInterval(g_interval);
	g_running = 0;
	document.getElementById("initButton").disabled = false;
	document.getElementById("stepButton").disabled = false;

}

function stepSim() {
	var neighbor = 0;
	g_tick++;

	//~ for (var x = 0; x < g_width; x++) {
	for (var x = g_width-1; x >= 0; x-- ) { 
		for (var y = 0; y < g_height; y++) {
			var agentCoords = [x, y];
			var neighborCoords = selectNeighbor(agentCoords);
			communicate(agentCoords, neighborCoords); 
			//~ console.log("agent " + agentCoords + " is now talking to " + neighborCoords);
		}
	}
	drawToCanvas();
}


function selectDirectNeighbor(x, y) {
	var neighbors = [[x-1,y], [x,y-1], [x+1,y], [x,y+1], [x-1,y-1], [x+1,y-1], [x-1,y+1], [x+1,y+1]];
	
	// retry if coords are out of bounds
	var i = 0;
	do { i = Math.floor((Math.random()*1000)%8);
	} 
	while (! borderCheck(neighbors[i]));
	return neighbors[i];
}

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
function borderCheck(xy) {
	var x = xy[0];
	var y = xy[1];
	if (x < 0) return false;
	if (y < 0) return false;
	if (x >= g_width) return false;
	if (y >= g_height) return false;
	return true;
}

function isValidNeighbor(coords1, coords2) {
    if (!borderCheck(coords2)) return false;
    if (coords1[0] == coords2[0] && coords1[1] == coords2[1]) return false;
    return true;
}

// alternative code to find neighbor, does not need to be direct neighbor but up to n positions away
// closer ones should be more likely to be chosen
function selectNeighbor(thisAgent) {
	var x_offset;
	var y_offset;
	var thisNeighbor;

	// retry if coords are out of bounds
	do { 
		x_offset = findNeighborOffset(g_neighborRange);
		y_offset = findNeighborOffset(g_neighborRange);
		thisNeighbor = [thisAgent[0]+x_offset,thisAgent[1]+y_offset];
	} 
	while (! isValidNeighbor(thisAgent, thisNeighbor));
	return thisNeighbor;
}

// calculate by how much this neighbor's coordinate shall be offset
// using an exponential function, so that closer ones are more likely to be selected
//  y = r^2*7
// 50% chance of negative value
function findNeighborOffset(max) {
	var v = Math.round(Math.pow(Math.random(), 2) * max) ;
	if (Math.floor(Math.random() * 2) === 1) v = v * -1;
	return v;
}

function communicate(agentCoords, neighborCoords) {
	var utteranceAgent = produceUtterance(agentCoords);
	var utteranceNeighbor = produceUtterance(neighborCoords);
	
	var xAgent = agentCoords[0];
	var yAgent = agentCoords[1];
	
	var xNeighbor = neighborCoords[0];
	var yNeighbor = neighborCoords[1];
	
	//store in memory
	var agentMemory = truncateMemory(applyError(utteranceNeighbor) + g_myMatrix[xAgent][yAgent][1]);
	var neighborMemory = truncateMemory(applyError(utteranceAgent) + g_myMatrix[xNeighbor][yNeighbor][1]);
	
	// adapt grammar
	var agentGrammar = g_myMatrix[xAgent][yAgent][0];
	var neighborGrammar = g_myMatrix[xNeighbor][yNeighbor][0];
	
	var agentGrammarNew = agentGrammar + g_lambda*(countARatio(agentMemory) - agentGrammar);
	var neighborGrammarNew = neighborGrammar + g_lambda*(countARatio(neighborMemory) - neighborGrammar);

	g_myMatrix[xAgent][yAgent] = [agentGrammarNew, agentMemory];
	g_myMatrix[xNeighbor][yNeighbor] = [neighborGrammarNew, neighborMemory];

}

function produceUtterance(agentCoords) {
	var x = agentCoords[0];
	var y = agentCoords[1];
	var u = "";
	for (var i = 0; i < 10; i++) {
		var myRand = Math.random();
		var agentGrammar = g_myMatrix[x][y][0];
		if (myRand <= agentGrammar * g_alphaBias) u += "α"; 
		else u += "β"; 
	}
	return u;
}

function countARatio(memory) {
	var counter = 0;
	for (var i = 0; i < memory.length; i++) {
		if (memory.charAt(i) === "α") counter++;
	}
	return counter/memory.length;
	
}

function truncateMemory(memory) {
	if (memory.length > g_memoryLimit) memory = memory.substring(0, g_memoryLimit); 
	return memory;
}

function applyError(s) { // (potentially) introduce misunderstandings between speaker and hearer
	var result = "";
	for (var i = 0; i < s.length; i++) {
		var thisChar = s[i];
		var thisResultChar = thisChar;
		if (Math.random() < g_errorRate) {
			if (thisChar === "α") thisResultChar = "β";
			else  thisResultChar = "α";
			//~ console.log("error! speaker said: " + thisChar + ", but hearer heard: " + thisResultChar);
		}
		result += thisResultChar;
	}
	return result;
}

function drawToCanvas() {
	var myCanvas = document.getElementById("simCanvas");
	var myContext = myCanvas.getContext("2d");
	
	var sumGValues = 0;

	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			var p = g_myMatrix[x][y][0];
			var green = Math.floor(128*p); // green according to CSS color definition
			var red = Math.floor(255*(1-p));
			var color = "rgb(" + red + "," + green + ", 0)";
			myContext.fillStyle = color;
			myContext.fillRect(x*4, y*4, 4, 4);
			
			sumGValues += p;
		}
	}
	document.getElementById('ticks').innerHTML = g_tick;
	
	// plot
	var plotCanvas = document.getElementById("plotCanvas");
	var plotContext = plotCanvas.getContext("2d");
	var sumAgents = g_width * g_height;
	var alpha_y = 100/sumAgents*sumGValues;
	var beta_y = 100/sumAgents*(sumAgents - sumGValues);
	
	plotContext.fillStyle = "green";
	plotContext.fillRect(g_tick+5, 100-alpha_y, 2, 2);
	plotContext.fillStyle = "red";
	plotContext.fillRect(g_tick+5, 100-beta_y, 2, 2);
}

