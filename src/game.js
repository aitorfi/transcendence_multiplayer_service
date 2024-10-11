'use strict'

import { getGamePositions, join, button } from "./com.js";

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

//constants  
const BALL_SIZE = 10;
const PADDLE_SPEED = 6;
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
	deactivateKeydown();
	updateScore();
    gameLoop();
}

async function otraFuncion() {
    // Hacer algo asíncrono
	showWinMessage("3");
    await new Promise((resolve) => setTimeout(resolve, 800));
	showWinMessage("2");
	await new Promise((resolve) => setTimeout(resolve, 800));
	showWinMessage("1");
	await new Promise((resolve) => setTimeout(resolve, 800));
}

// Llamar a otraFuncion y luego ejecutar refresh
async function ejecutar() {
    await otraFuncion();
    refresh();
}

function handleSpacePress(event) {
    if (event.key === ' ') {
        initializeGame();
    }
}

function deactivateKeydown() {
	document.removeEventListener('keydown', handleSpacePress);
}

function gameLoop() {
	
	cleanCanva();
	drawCanva();
	
	if (wait == true)
	{
		if (finish) {
            terminateGame();
            // Añadimos el listener para la tecla 'space'
            document.addEventListener('keydown', handleSpacePress);
        }
		else
			ejecutar();
		wait = false;
	}
	else
		refresh();
}

function drawRect(x, y, w, h, color) {
	ctx.fillStyle = color;
	ctx.fillRect(x, y, w, h);
}

function drawBall(x, y, size, color) {
	ctx.fillStyle = color;
	ctx.beginPath();
	ctx.arc(x, y, size, 0, Math.PI * 2);
	ctx.fill();
}

function cleanCanva()
{
	ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawCanva()
{
	gameCoord = getGamePositions();
	drawRect(0, gameCoord[2], PADDLE_WIDTH, PADDLE_HEIGHT, 'white');
	drawRect(canvas.width - PADDLE_WIDTH, gameCoord[3], PADDLE_WIDTH, PADDLE_HEIGHT, 'white');
	drawBall(gameCoord[0], gameCoord[1], BALL_SIZE, 'white');
	//drawBall(ballX, ballY, BALL_SIZE, 'white');
}

function updateScore()
{
	document.getElementById('player1-score').textContent = 'Player 1: ' + player1Score;
	document.getElementById('player2-score').textContent = 'Player 2: ' + player2Score;
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

function showWinMessage(message) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'white';
    ctx.font = '30px Arial';
    ctx.textAlign = 'center';

    // Dividimos el mensaje en líneas, usando "\n" como separador
    const lines = message.split('\n');
    
    // Para centrar cada línea verticalmente, ajustamos la posición Y para cada línea
    lines.forEach((line, index) => {
        ctx.fillText(line, canvas.width / 2, canvas.height / 2 + (index * 40)); // Ajusta el valor 40 para el espaciado entre líneas
    });
}


