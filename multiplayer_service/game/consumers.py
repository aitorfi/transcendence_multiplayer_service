import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asyncio import sleep

# Diccionario global para mantener a los jugadores esperando
waiting_players = []

# Diccionario para almacenar las salas activas (por simplicidad, puede ser reemplazado por una base de datos)
active_rooms = {}

class GameMatchmakingConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		"""Cuando un cliente se conecta al WebSocket."""
		await self.accept()  # Acepta la conexión del WebSocket

	async def disconnect(self, close_code):
		"""Cuando el cliente se desconecta."""
		# Remover al jugador de la lista de espera si aún no se ha emparejado
		if self in waiting_players:
			waiting_players.remove(self)
        
		# Si está en una sala, removerlo de la misma
		for room_id, players in active_rooms.items():
			if self in players:
				active_rooms[room_id].remove(self)

				# Notificar al otro jugador que la sala se ha cerrado
				if len(active_rooms[room_id]) == 1:
					await active_rooms[room_id][0].send(text_data=json.dumps({
						'type': 'game_end',
						'message': 'El otro jugador se ha desconectado. Fin de la partida.'
					}))
				# Si la sala está vacía, eliminarla
				if len(active_rooms[room_id]) == 0:
					del active_rooms[room_id]
				break

	async def receive(self, text_data):
		"""Manejar mensajes recibidos de los jugadores."""
		data = json.loads(text_data)
		message_type = data.get('type', 0)

		if message_type == 'join_game':
			await self.handle_action_join_game(data)
		elif message_type == 'move':
			await self.handle_action_player_movement(data)
		else:
			await self.send(text_data=json.dumps({
				'type': 'error',
				'message': "Bad request, parameter 'type' is mandatory"
			}))

	async def handle_action_join_game(self, data):
		self.user_id = data.get('user_id', 0)
		if self.user_id:
			waiting_players.append(self)
			await self.match_players()
		else:
			await self.send(text_data=json.dumps({
				'type': 'error',
				'message': "Bad request, parameter 'user_id' is mandatory"
			}))

	async def match_players(self):
		"""Intenta emparejar jugadores en la lista de espera."""
		if len(waiting_players) >= 2:  # Necesitamos al menos dos jugadores para emparejar
			# Emparejar a los dos primeros jugadores
			player1 = waiting_players.pop(0)
			player2 = waiting_players.pop(0)
			
			await self.init_new_game(player1, player2)
			await self.notify_match_found(player1, player2)
			await sleep(1)
			await self.notify_start_game(player1, player2)

	async def init_new_game(self, player1, player2):
		# Crear una nueva sala para la partida
		room_id = f"room_{player1.user_id}_{player2.user_id}"

		# active_rooms[room_id] = [player1, player2]
		active_rooms[room_id] = {
			'player1': player1,
			'player2': player2,
			'game_state': {
				'player1Y': 25,
				'player2Y': 25,
				'ball': {
					'position': {'x': 50, 'y': 25},
					'speed': {'x': 1, 'y': 1}
				}
			}
		}
		
		player1.room_id = room_id
		player2.room_id = room_id

	async def notify_match_found(self, player1, player2):
		# Notificar a ambos jugadores que están emparejados y la partida va a empezar
		await player1.send(text_data=json.dumps({
			'type': 'match_found',
			'room': player1.room_id
		}))
		await player2.send(text_data=json.dumps({
			'type': 'match_found',
			'room': player2.room_id
		}))

	async def notify_start_game(self, player1, player2):
		# Iniciar el juego enviando un mensaje de sincronización a ambos jugadores
		await player1.send(text_data=json.dumps({
			'type': 'start_game'
		}))
		await player2.send(text_data=json.dumps({
			'type': 'start_game'
		}))

	async def handle_action_player_movement(self, data):
		room = active_rooms.get(self.room_id, [])
		movement_direction = data.get('direction', 0)
		is_player1 = room['player1'].user_id == self.user_id
		if movement_direction == 'up':
			if is_player1:
				room['game_state']['player1Y'] -= 1
			else:
				room['game_state']['player2Y'] -= 1
		elif movement_direction == 'down':
			if is_player1:
				room['game_state']['player1Y'] += 1
			else:
				room['game_state']['player2Y'] += 1
		else:
			await self.send(text_data=json.dumps({
				'type': 'error',
				'message': "Bad request, parameter 'direction' is mandatory."
			}))
			return
		await self.send_game_state_update(room)

	async def send_game_state_update(self, room):
		await room['player1'].send(text_data=json.dumps({
			'type': 'game_state_update',
			'game_state': room['game_state']
		}))
		await room['player2'].send(text_data=json.dumps({
			'type': 'game_state_update',
			'game_state': room['game_state']
		}))
