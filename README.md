# Como usar el proyecto

## Dependencias

Para usar el proyecto hay que instalar los paquetes `channels` y `daphne` de python:
        aiohttp -> lo utilizaremos para pasar 
            los datos de las partidas del servidor de partidas al backend de torneos
            
```bash
pip install channels daphne aiohttp   

```

## Ejecutar el servidor

Para ejecutar el servidor hay que posicionarse en la carpeta del proyecto de Django `multiplayer_service` y lanzar el siguiente comando:

```bash
daphne -p 50002 multiplayer_service.asgi:application

python3 -m daphne -p 50002 multiplayer_service.asgi:application //Este si, el anterior no va

python3 -m daphne -b 0.0.0.0 -p 50002 multiplayer_service.asgi:application # Este
#expone daphne para que se pueda acceder desde otro puesto
```

## Testeo

He hecho un pequeño html con código JavaScript que se puede usar para testear el servicio y como plantilla para saber como hacer las llamadas al servicio. Solo hay que copiar el código a un fichero html (puede estar ubicado en cualquier sitio, mejor si no lo meteis dentro del proyecto por si lo subís al repo sin querer) y lanzar un servidor (la extension de Live Server por ejemplo):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Test</title>
</head>
<body>
    <h1>WebSocket Pong Game</h1>
		<input type="text" id="user_id_txt_field">
		<button id="join_game">Buscar partida</button>
		<button id="move_up">Moverse arriba</button>
		<button id="move_down">Moverse abajo</button>
    <script>
        const socket = new WebSocket('ws://localhost:50002/ws/game/');

        socket.onopen = function(e) {
            console.log("Conectado al WebSocket");
        };

        socket.onmessage = function(event) {
            console.log("Mensaje del servidor:", event.data);
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

				document.getElementById("join_game").onclick = () => {
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
        };
    </script>
</body>
</html>
```
