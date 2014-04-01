var g_myMatrix;
var g_width = 40;
var g_height = 40;

var g_interval;
var g_running = 0;

var g_lambda = 0.05;
var g_memoryLimit = 200;

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


function initSim() {
	var myCanvas = document.getElementById("simCanvas");
	var myContext = myCanvas.getContext("2d");

	g_myMatrix = matrix(g_height, g_width, 0);// initial probability, initial memory
	
	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			//~ console.log("pInit:" + pInit);
			g_myMatrix[x][y] = [0.5 + (Math.random() - 0.5)/4, ""];
			//~ console.log("g_myMatrix[x][y][0]:" + g_myMatrix[x][y][0]);
		}
	}

	drawToCanvas();
}

function runSim() { // run or stop
	if (!g_running) {
		 g_interval = setInterval(stepSim,500);
		 g_running = 1;
	} else {
		clearInterval(g_interval);
		g_running = 0;
	}
}

function stepSim() {
	var neighbor = 0;

	// zwischenspeichern
	newMatrix = matrix(g_height, g_width, [0, ""]);

	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			var agentCoords = [x, y];
			var neighborCoords = selectNeighbor(x, y);
			communicate(agentCoords, neighborCoords, newMatrix); 
		}
	}
	g_myMatrix = newMatrix;
	drawToCanvas();
}

function selectNeighbor(x, y) {
	var i = Math.floor((Math.random()*1000)%8);
	var neighbors = [[x-1,y], [x,y-1], [x+1,y], [x,y+1], [x-1,y-1], [x+1,y-1], [x-1,y+1], [x+1,y+1]];
	
	return borderCheck(neighbors[i]);
}

function borderCheck(xy) {
	var x = xy[0];
	var y = xy[1];
	if (x < 0) x = g_width - 1;
	if (y < 0) y = g_height - 1;
	if (x == g_width) x = 0;
	if (y == g_height) y = 0;
	return [x, y];
}

function communicate(agentCoords, neighborCoords, newMatrix) {
	var utteranceAgent = produceUtterance(agentCoords);
	var utteranceNeighbor = produceUtterance(neighborCoords);
	
	var xAgent = agentCoords[0];
	var yAgent = agentCoords[1];
	
	var xNeighbor = neighborCoords[0];
	var yNeighbor = neighborCoords[1];
	
	//store in memory
	var agentMemory = truncateMemory(utteranceNeighbor + g_myMatrix[xAgent][yAgent][1]);
	var neighborMemory = truncateMemory(utteranceAgent + g_myMatrix[xNeighbor][yNeighbor][1]);
	
	// adapt grammar
	var agentGrammar = g_myMatrix[xAgent][yAgent][0];
	var neighborGrammar = g_myMatrix[xNeighbor][yNeighbor][0];
	
	var agentGrammarNew = agentGrammar + g_lambda*(countARatio(agentMemory) - agentGrammar);
	var neighborGrammarNew = neighborGrammar + g_lambda*(countARatio(neighborMemory) - neighborGrammar);

	newMatrix[xAgent][yAgent] = [agentGrammarNew, agentMemory];
	newMatrix[xNeighbor][yNeighbor] = [neighborGrammarNew, neighborMemory];
}

function produceUtterance(agentCoords) {
	var x = agentCoords[0];
	var y = agentCoords[1];
	var u = "";
	for (var i = 0; i < 10; i++) {
		var myRand = Math.random();
		var p = g_myMatrix[x][y][0];
		if (myRand <= p) u += "α"; 
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

function drawToCanvas() {
	var myCanvas = document.getElementById("simCanvas");
	var myContext = myCanvas.getContext("2d");

	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			var color = "yellow";
			//~ console.log("g_myMatrix[x][y][0]:" + g_myMatrix[x][y][0]);
			if (g_myMatrix[x][y][0] <= 0.45) color = "green";
			if (g_myMatrix[x][y][0] >= 0.55) color = "red";
			myContext.fillStyle = color;
			myContext.fillRect(x*4, y*4, 4, 4);
		}
	}
}
