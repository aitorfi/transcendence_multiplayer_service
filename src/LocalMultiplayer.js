'use strict'

//Game variables
let canvas;
let ctx;
let player1Y, player2Y;
let ballX, ballY;
let ballSpeedX, ballSpeedY;
let player1Up, player1Down;
let player2Up, player2Down;
let gameLoopId;
let timeoutId;
let player1Score;
let player2Score;
let wait;
let finish;

//constants  
const BALL_SIZE = 10;
const PADDLE_SPEED = 6;
const PADDLE_HEIGHT = 100;
const PADDLE_WIDTH = 10;
const BALL_DIR_RIGHT = '+';
const BALL_DIR_LEFT = '-';
const BALL_DIR_UP = '-';
const BALL_DIR_DOWN = '+';
const SPEED_INC = 0.15;
const ANGLE_INC = 0.4;


export function initializeGame() {
	canvas = document.getElementById('pongCanvas');
	ctx = canvas.getContext('2d');
	setBallSpeed();
	player1Up = false;
	player1Down = false;
	player2Up = false;
	player2Down = false;
	player1Score = 0;
	player2Score = 0;
	wait = false;
	finish = false;

	// calculo para encontrar el punto medio de una superficie disponible
    player1Y = (canvas.height - PADDLE_HEIGHT) / 2;
    player2Y = (canvas.height - PADDLE_HEIGHT) / 2;
    ballX = canvas.width / 2 /*- BALL_SIZE / 2;*/
    ballY = canvas.height / 2 /*- BALL_SIZE / 2;*/

    document.addEventListener('keydown', (event) => {
		if (event.key === 'w') player1Up = true;
		if (event.key === 's') player1Down = true;
		if (event.key === 'ArrowUp') player2Up = true;
		if (event.key === 'ArrowDown') player2Down = true;
    });

    document.addEventListener('keyup', (event) => {
		if (event.key === 'w') player1Up = false;
		if (event.key === 's') player1Down = false;
		if (event.key === 'ArrowUp') player2Up = false;
		if (event.key === 'ArrowDown') player2Down = false;
    });

	const h1Element = document.querySelector('#pong-container h1');
	  // Cambia el texto del h1
	h1Element.textContent = 'Local Multiplayer';

	wait = true;
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
	updatePlayerAndBall();
	checkLowerAndUpperCollision();
	checkLeftAndRightCollision();
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
	drawRect(0, player1Y, PADDLE_WIDTH, PADDLE_HEIGHT, 'white');
	drawRect(canvas.width - PADDLE_WIDTH, player2Y, PADDLE_WIDTH, PADDLE_HEIGHT, 'white');
	drawBall(ballX, ballY, BALL_SIZE, 'white');
}

function updatePlayerAndBall()
{
	if (player1Up && player1Y > 0)
		player1Y -= PADDLE_SPEED;
	if (player1Down && player1Y < canvas.height -PADDLE_HEIGHT)
		player1Y += PADDLE_SPEED;
	if (player2Up && player2Y > 0)
		player2Y -= PADDLE_SPEED;
	if (player2Down && player2Y < canvas.height - PADDLE_HEIGHT)
		player2Y += PADDLE_SPEED;
	ballX += ballSpeedX;
	ballY += ballSpeedY;
}

function checkLowerAndUpperCollision()
{
	if (ballY - BALL_SIZE <= 0 || ballY + BALL_SIZE >= canvas.height)
		ballSpeedY = -ballSpeedY;
}


function leftCollision()
{
	if (ballX <= PADDLE_WIDTH) {
		if (ballY > player1Y && ballY < player1Y + (PADDLE_HEIGHT / 3))
		{
			ballSpeedX = -ballSpeedX;
			ballX += 0.5;
			console.log("y = ",  Math.abs(ballSpeedY).toFixed(3), " x = ",  Math.abs(ballSpeedX).toFixed(3));
			if (ballSpeedY <= 0)
			{
				if (Math.abs(ballSpeedY) < Math.abs(ballSpeedX))
				{
					ballSpeedY = ballSpeedY - ANGLE_INC;
					ballSpeedX = ballSpeedX - ANGLE_INC;
				}
			}
			else
			{
				ballSpeedY = ballSpeedY - ANGLE_INC;
				ballSpeedX = ballSpeedX + ANGLE_INC;
			}

		}
		else if (ballY > player1Y +  (PADDLE_HEIGHT / 3) && ballY < player1Y + ((PADDLE_HEIGHT / 3) * 2))
		{
			ballSpeedX = -ballSpeedX;
		}
		else if (ballY > player1Y + ((PADDLE_HEIGHT / 3) * 2) && ballY < player1Y + PADDLE_HEIGHT)
		{
			ballSpeedX = -ballSpeedX;
			ballX += 0.5;
			console.log("y = ",  Math.abs(ballSpeedY).toFixed(3), " x = ",  Math.abs(ballSpeedX).toFixed(3));
			if (ballSpeedY <= 0)
			{
				ballSpeedY = ballSpeedY + ANGLE_INC;
				ballSpeedX = ballSpeedX + ANGLE_INC;
			}
			else
			{
				if(Math.abs(ballSpeedY) < Math.abs(ballSpeedX))
				{
					ballSpeedY = ballSpeedY + ANGLE_INC;
					ballSpeedX = ballSpeedX - ANGLE_INC;
				}
			}
		}
		else
		{
			player2Score++;
			if(player2Score == 3)
			{
				showWinMessage("Player 2 wins!\nPush space to play again");
				finish = true;
			}
			updateScore();
			resetBall();
			resetPlayerPositions();
			wait = true;
			return;
		}
		ballSpeedX += SPEED_INC;
		if(ballSpeedY <= 0)
			ballSpeedY -= SPEED_INC;
		else
			ballSpeedY += SPEED_INC;
	}
}

function rightCollision()
{
	if (ballX >= canvas.width - PADDLE_WIDTH) {
		if (ballY > player2Y && ballY < player2Y + (PADDLE_HEIGHT / 3))
		{
			ballSpeedX = -ballSpeedX;
			ballX -= 0.5;
			console.log("y = ",  Math.abs(ballSpeedY).toFixed(3), " x = ",  Math.abs(ballSpeedX).toFixed(3));
			if (ballSpeedY <= 0)
			{
				if(Math.abs(ballSpeedY) < Math.abs(ballSpeedX))
				{
					ballSpeedY = ballSpeedY - ANGLE_INC;
					ballSpeedX = ballSpeedX + ANGLE_INC;
				}
			}
			else
			{
				ballSpeedY = ballSpeedY - ANGLE_INC;
				ballSpeedX = ballSpeedX - ANGLE_INC;	
			}
		}
		else if (ballY > player2Y + (PADDLE_HEIGHT / 3) && ballY < player2Y + ((PADDLE_HEIGHT / 3) * 2))
		{
			ballSpeedX = -ballSpeedX;
		}
		else if (ballY > player2Y + ((PADDLE_HEIGHT / 3) * 2) && ballY < player2Y + PADDLE_HEIGHT)
		{
			ballSpeedX = -ballSpeedX;
			ballX -= 0.5;
			console.log("y = ",  Math.abs(ballSpeedY).toFixed(3), " x = ",  Math.abs(ballSpeedX).toFixed(3));
			if (ballSpeedY <= 0)
			{
				ballSpeedY = ballSpeedY + ANGLE_INC;
				ballSpeedX = ballSpeedX - ANGLE_INC;
			}
			else
			{
				if (Math.abs(ballSpeedY) < Math.abs(ballSpeedX))
				{
					ballSpeedY = ballSpeedY + ANGLE_INC;
					ballSpeedX = ballSpeedX + ANGLE_INC;
				}
			}
		}
		else
		{
			player1Score++;
			if(player1Score == 3)
			{
				showWinMessage("Player 1 wins!\nPush space to play again");
				finish = true;
			}
			updateScore();
			resetBall();
			resetPlayerPositions();
			wait = true;
			//showWinMessage("Player 1 wins");
			return;
		}
		ballSpeedX -= SPEED_INC;
		if(ballSpeedY <= 0)
			ballSpeedY -= SPEED_INC;
		else
			ballSpeedY += SPEED_INC;
	}
}

function checkLeftAndRightCollision()
{
	leftCollision();
	rightCollision();  
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

function resetBall()
{
	ballX = canvas.width / 2;
	ballY = canvas.height / 2;
	setBallSpeed();
}

function resetPlayerPositions()
{
	player1Y = (canvas.height - PADDLE_HEIGHT) / 2;
    player2Y = (canvas.height - PADDLE_HEIGHT) / 2;
}

function updateScore()
{
	document.getElementById('player1-score').textContent = 'Player 1: ' + player1Score;
	document.getElementById('player2-score').textContent = 'Player 2: ' + player2Score;
}

function refresh() {
	gameLoopId = requestAnimationFrame(gameLoop);
}

function getDirectionSideForBall()
{
	return Math.random() < 0.5 ? BALL_DIR_RIGHT : BALL_DIR_LEFT;
}

function getDirectionUpOrDownBall()
{
	return Math.random() < 0.5 ? BALL_DIR_UP : BALL_DIR_DOWN;
}

function setBallSpeed()
{
	let ballDirSideways = getDirectionSideForBall();
	let ballDirUpOrDown = getDirectionUpOrDownBall();
	ballSpeedX = 4;
	if (ballDirSideways == BALL_DIR_LEFT)
		ballSpeedX = (-1) * ballSpeedX;
	ballSpeedY = 1;
	if (ballDirUpOrDown == BALL_DIR_UP)
		ballSpeedY = (-1) * ballSpeedY;
}