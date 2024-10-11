'use strict'


const socket = new WebSocket('ws://10.14.2.1:50002/ws/game/');


const campoUserId = document.getElementById('user_id_txt_field');

let user_id;
let type;
let ballx;
let bally;
let Player1Y;
let Player2Y;
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
        ballx = mensaje.game_state.ball.position.x;
        bally = mensaje.game_state.ball.position.y;
        Player1Y = mensaje.game_state.player1Y;
        Player2Y = mensaje.game_state.player2Y;
        //imprimirEnPantalla(mensaje.game_state.ball.position.x, mensaje.game_state.ball.position.y);
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
}

// Llamada a la función para mostrar un mensaje de prueba
imprimirEnPantalla("Aqui mostramos posicion x de la bola.", "Aqui mostramos posicion y de la bola."); */
