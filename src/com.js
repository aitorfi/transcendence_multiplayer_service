'use strict'

import { updateScore } from "./game.js";

//const socket = new WebSocket('ws://10.14.2.1:50002/ws/game/');
const socket = new WebSocket('ws://127.0.0.1:50002/ws/game/');

const campoUserId = document.getElementById('user_id_txt_field');

let user_id;
let type;
export let game_state = "waiting";
export let screen_mesagge = "Waiting another player to join the game";
export let color = "yellow";
export let ballx;
export let bally;
export let Player1Y;
export let Player2Y;
export let Player1Points = 0;
export let Player2Points = 0;
let coord;

export function getGamePositions()
{
    coord = [ballx, bally, Player1Y, Player2Y];
	return coord;
}

export async function button(b)
{
    socket.send(JSON.stringify({
        type: 'move',
        action: b
    }));

}

export function join()
{
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
                            type: "join_game",
                            user_id: "12"
                        }));
    }
}

socket.onopen = function(e) {
    console.log("Conectado al WebSocket");
};

socket.onmessage = function(event) {
    //console.log("Mensaje del servidor:", event.data);
    const mensaje = JSON.parse(event.data);
    if(mensaje.type == "game_state_update")
    {
        ballx = mensaje.ballX;
        bally = mensaje.ballY;
        Player1Y = mensaje.player1Y;
        Player2Y = mensaje.player2Y;
        //console.log("game update");
    }
    else if (mensaje.type == "start_game")
        game_state = "playing";
    else if (mensaje.type =="match_found")
    {
        screen_mesagge = mensaje.messagge;
        color = mensaje.color;
    }
    else if (mensaje.type =="new_message")
    {
        screen_mesagge = mensaje.messagge;
        color = mensaje.color;
    }
    else if (mensaje.type =="finish")
    {
        game_state = "waiting";
        screen_mesagge = mensaje.messagge;
        color = mensaje.color;
        Player1Points = mensaje.player1Points;
        Player2Points = mensaje.player2Points;
        updateScore();
    }
    else if (mensaje.type =="update")
    {
        game_state = "waiting";
        Player1Points = mensaje.player1Points;
        Player2Points = mensaje.player2Points;
        updateScore();
    }
};

socket.onclose = function(event) {
    if (event.wasClean) {
        console.log(`Conexión cerrada limpiamente, código: ${event.code}, motivo: ${event.reason}`);
    } else {
        console.log("Conexión terminada");
    }
};

socket.onerror = function(error) {
    console.log("Error en el WebSocket", error);
};


/* document.getElementById("join_game").onclick = () => {
    user_id = document.getElementById('user_id_txt_field').value;
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
                            type: "join_game",
                            user_id: user_id
                        }));
    }
};

document.getElementById("move_up").onclick = () => {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
                            type: "move",
                            direction: "up"
                        }));
    }
};

document.getElementById("move_down").onclick = () => {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
                            type: "move",
                            direction: "down"
                        }));
    }
}; */

// Función para imprimir un mensaje en el contenedor de la pantalla
/* function imprimirEnPantalla(mensaje1, mensaje2) {
    // Selecciona el contenedor por su ID
    const contenedor = document.getElementById("mensajeContainer");
    const contenedor2 = document.getElementById("mensajeContainer2");

    // Inserta el mensaje en el contenedor
    contenedor.innerHTML = `<p>x = ${mensaje1}</p>`;
    contenedor2.innerHTML = `<p>y = ${mensaje2}</p>`; // Agrega un nuevo párrafo con el mensaje
} */

// Llamada a la función para mostrar un mensaje de prueba
//imprimirEnPantalla("Aqui mostramos posicion x de la bola.", "Aqui mostramos posicion y de la bola.");
