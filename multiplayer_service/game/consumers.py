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
		message_type = data.get('type')

		if message_type == 'join_game':
			self.user_id = data['user_id']
			waiting_players.append(self)
			await self.match_players()
		elif message_type == 'move':
			# Manejar la acción de movimiento del jugador
			# Transmitir el movimiento al otro jugador en la misma sala
			room = active_rooms.get(self.room_name, [])
			for player in room:
				if player != self:
					await player.send(text_data=json.dumps({
						'type': 'opponent_move'
					}))

	async def match_players(self):
		"""Intenta emparejar jugadores en la lista de espera."""
		if len(waiting_players) >= 2:  # Necesitamos al menos dos jugadores para emparejar
			# Emparejar a los dos primeros jugadores
			player1 = waiting_players.pop(0)
			player2 = waiting_players.pop(0)
			
			# Crear una nueva sala para la partida
			room_id = f"room_{player1.user_id}_{player2.user_id}"
			active_rooms[room_id] = [player1, player2]
			
			# Asignar la sala a ambos jugadores
			player1.room_name = room_id
			player2.room_name = room_id
			
			# Notificar a ambos jugadores que están emparejados y la partida va a empezar
			await player1.send(text_data=json.dumps({
				'type': 'match_found',
				'room': room_id,
				'message': f'Partida encontrada user_1 = {player1.user_id} user_2 = {player2.user_id}'
			}))
			await player2.send(text_data=json.dumps({
				'type': 'match_found',
				'room': room_id,
				'message': f'Partida encontrada user_1 = {player1.user_id} user_2 = {player2.user_id}'
			}))

			# Esperar un breve tiempo para asegurar la sincronización (puedes ajustar este valor)
			await sleep(1)

			# Iniciar el juego enviando un mensaje de sincronización a ambos jugadores
			await player1.send(text_data=json.dumps({
				'type': 'start_game',
				'message': 'El juego comienza ahora.'
			}))
			await player2.send(text_data=json.dumps({
				'type': 'start_game',
				'message': 'El juego comienza ahora.'
			}))
