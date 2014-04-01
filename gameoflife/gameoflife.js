var g_myMatrix;
var g_width = 40;
var g_height = 40;

var g_interval;
var g_running = 0;


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

	g_myMatrix = matrix(g_height, g_width, 0);
	
	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			g_myMatrix[x][y] = Math.floor((Math.random()*100)%2); 
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
	var neighbors = 0;

	// zwischenspeichern
	newMatrix = matrix(g_height, g_width, 0);

	
	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			neighbors = calcNeighbors(x, y);
			if (neighbors == 3) newMatrix[x][y] = 1;
			else if (neighbors == 2) newMatrix[x][y] = g_myMatrix[x][y];
			else newMatrix[x][y] = 0;
		}
	}
	//g_myMatrix = newMatrix.slice(0);
	g_myMatrix = newMatrix;
	drawToCanvas();
}

function calcNeighbors(x, y) {
	var neighbors = 0;
	if (checkNeighbor(x-1,y)) neighbors++; //left
	if (checkNeighbor(x,y-1)) neighbors++; //top
	if (checkNeighbor(x+1,y)) neighbors++; //right
	if (checkNeighbor(x,y+1)) neighbors++; // bottom
	if (checkNeighbor(x-1,y-1)) neighbors++; //top-left
	if (checkNeighbor(x+1,y-1)) neighbors++; //top-right
	if (checkNeighbor(x-1,y+1)) neighbors++; //bottom-left
	if (checkNeighbor(x+1,y+1)) neighbors++; //bottom-right
	
	return neighbors;
}

function checkNeighbor(x, y) {
	if (x < 0) x = g_width - 1;
	if (y < 0) y = g_height - 1;
	if (x == g_width) x = 0;
	if (y == g_height) y = 0;
	return g_myMatrix[x][y];
}

function drawToCanvas() {
	var myCanvas = document.getElementById("simCanvas");
	var myContext = myCanvas.getContext("2d");

	for (var x = 0; x < g_width; x++) {
		for (var y = 0; y < g_height; y++) {
			var color = "#FFF";
			if (g_myMatrix[x][y] === 0) color = "#000";
			myContext.fillStyle = color;
			myContext.fillRect(x*4, y*4, 4, 4);
		}
	}
}
