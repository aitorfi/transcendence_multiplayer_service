'use strict'

import { getGamePositions, join, button } from "./com.js";
import { game_state,ballx, bally, Player1Y, Player2Y, screen_mesagge, color, Player1Points, Player2Points } from "./com.js";
//Game variables
let canvas;
let ctx;
let player1Up, player1Down;
let player2Up, player2Down;
let gameLoopId;
let timeoutId;
let player1Score;
let player2Score;
let wait;
let finish;
let gameCoord;
let connect = 0;
let x;


//constants  
const BALL_SIZE = 10;
//const PADDLE_SPEED = 6;
const PADDLE_HEIGHT = 100;
const PADDLE_WIDTH = 10;



export function initializeGame() {
	canvas = document.getElementById('pongCanvas');
	ctx = canvas.getContext('2d');
	player1Up = false;
	player1Down = false;
	player2Up = false;
	player2Down = false;
	player1Score = 0;
	player2Score = 0;
	wait = false;
	finish = false;


    document.addEventListener('keydown', (event) => {
		if (event.key === 'w' && player1Up == false)
		{
			button("upOn");
			player1Up = true;
		}
		if (event.key === 's' && player1Down == false)
		{
			button("downOn");
			player1Down = true;
		} 

    });

    document.addEventListener('keyup', (event) => {
		if (event.key === 'w')
		{
			button("upOff");
			player1Up = false;
		}
		if (event.key === 's')
		{
			button("downOff");
			player1Down = false;
		}
		
    });

	const h1Element = document.querySelector('#pong-container h1');
	  // Cambia el texto del h1
	h1Element.textContent = 'Online Multiplayer';

	wait = true;

	gameCoord = [50, 50];
	
	if (connect == 0)
	{
		join();
		//join();
		connect = 1;
	}
	//deactivateKeydown();
	updateScore();
    gameLoop();
}


function gameLoop() {
	
	if(game_state == "playing")
	{
		if (x != ballx)
		{
			cleanCanva();
			console.log("PINTA!");
			x = ballx;
			drawCanva();
		}
		else
			console.log("NO PINTA!");
	}
	else if (game_state == "waiting")
		showMessage(screen_mesagge, color);

	refresh();	
}


/* function drawRect(x, y, w, h, color) {
	ctx.fillStyle = color;
	ctx.fillRect(x, y, w, h);
}

function drawBall(x, y, size, color) {
	
	ctx.fillStyle = color;
	ctx.beginPath();
	ctx.arc(x, y, size, 0, Math.PI * 2);
	ctx.fill();
} */

function drawRect(x, y) {
	ctx.fillStyle = 'white';
	ctx.fillRect(x, y, 10, 100);
}

function drawBall(x, y) {
	
	ctx.fillStyle = 'yellow';
	ctx.beginPath();
	ctx.arc(x, y, 10, 0, 6.28318);
	ctx.fill();
}

function drawDashedLine() {
    ctx.beginPath();
    ctx.setLineDash([5, 5]); // Define el patrón de línea discontinua
    ctx.moveTo(canvas.width / 2, 0); // Comienza en la parte superior
    ctx.lineTo(canvas.width / 2, canvas.height); // Termina en la parte inferior
    ctx.strokeStyle = 'white'; // Color de la línea
    ctx.lineWidth = 1; // Ancho de la línea
    ctx.stroke();
    ctx.setLineDash([]); // Restablece el patrón de línea a sólido
}

function cleanCanva()
{
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	//canvas.width = canvas.width;
}

function drawCanva()
{
	/* drawRect(0, Player1Y, PADDLE_WIDTH, PADDLE_HEIGHT, 'white');
	drawRect(canvas.width - PADDLE_WIDTH, Player2Y, PADDLE_WIDTH, PADDLE_HEIGHT, 'white');
	drawBall(ballx, bally, BALL_SIZE, 'white'); */
	drawRect(0, Player1Y);
	drawRect(590, Player2Y);
	drawDashedLine();
	drawBall(ballx, bally);
}

export function updateScore()
{
	document.getElementById('player1-score').textContent = 'Player 1: ' + Player1Points;
	document.getElementById('player2-score').textContent = 'Player 2: ' + Player2Points;
}

function refresh() {
	gameLoopId = requestAnimationFrame(gameLoop);
}

export function terminateGame() {
	document.removeEventListener('keydown', gameLoop);

	if (gameLoopId)
		cancelAnimationFrame(gameLoopId);
	if (timeoutId)
		clearTimeout(timeoutId);
}

function showMessage(message, color) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = color;
    ctx.font = '30px Arial';
    ctx.textAlign = 'center';

    // Dividimos el mensaje en líneas, usando "\n" como separador
    const lines = message.split('\n');
    
    // Para centrar cada línea verticalmente, ajustamos la posición Y para cada línea
    lines.forEach((line, index) => {
        ctx.fillText(line, canvas.width / 2, canvas.height / 2 + (index * 40)); // Ajusta el valor 40 para el espaciado entre líneas
    });
}


