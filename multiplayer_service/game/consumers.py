import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

# Diccionario global para mantener a los jugadores esperando
waiting_players = []

# Diccionario para almacenar las salas activas (por simplicidad, puede ser reemplazado por una base de datos)
active_rooms = {}

id = 1

class GameMatchmakingConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		"""Cuando un cliente se conecta al WebSocket."""
		print("se ha conectado un cliente")
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
		#self.user_id = data.get('user_id', 0)
		#global id
		message_id = data.get('user_id', 0)
		print (f"id = {message_id}")
		self.user_id = message_id
		#id += 1
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
			#await asyncio.sleep(1)
			asyncio.create_task(self.update_ball(self.room_id))
			await self.notify_start_game(player1, player2)

	async def init_new_game(self, player1, player2):
		# Crear una nueva sala para la partida
		room_id = f"room_{player1.user_id}_{player2.user_id}"

		# active_rooms[room_id] = [player1, player2]
		active_rooms[room_id] = {
			'player1': player1,
			'player2': player2,
			'game_state': {
				'player1Y': 150,
				'Player1Points': 0,
				'player1up': False,
				'player1down': False,
				'player2Y': 150,
				'Player2Points': 0,
				'player2up': False,
				'player2down': False,
				'paddleSpeed': 12,
				'ball': {
					'position': {'x': 300, 'y': 200},
					'speed': {'x': 10, 'y': 1}
				}
			}
		}
		
		player1.room_id = room_id
		player2.room_id = room_id

	async def countdown(self, player1, player2):
		await player1.send(text_data=json.dumps({
			'type': 'new_message',
			'messagge': '3',
			'color':  'palegreen'
		}))
		await player2.send(text_data=json.dumps({
			'type': 'new_message',
			'messagge': '3',
			'color':  'palegreen'
		}))
		await asyncio.sleep(1)
		await player1.send(text_data=json.dumps({
			'type': 'new_message',
			'messagge': '2',
			'color':  'palegreen'
		}))
		await player2.send(text_data=json.dumps({
			'type': 'new_message',
			'messagge': '2',
			'color':  'palegreen'
		}))
		await asyncio.sleep(1)
		await player1.send(text_data=json.dumps({
			'type': 'new_message',
			'messagge': '1',
			'color':  'palegreen'
		}))
		await player2.send(text_data=json.dumps({
			'type': 'new_message',
			'messagge': '1',
			'color':  'palegreen'
		}))
		await asyncio.sleep(1)
		await player1.send(text_data=json.dumps({
			'type': 'start_game',
		}))
		await player2.send(text_data=json.dumps({
			'type': 'start_game',
		}))
		

	async def notify_match_found(self, player1, player2):
		# Notificar a ambos jugadores que están emparejados y la partida va a empezar
		await player1.send(text_data=json.dumps({
			'type': 'match_found',
			'room': player1.room_id,
			'messagge': '¡Mach Found!',
			'color':  'palegreen'
		}))
		await player2.send(text_data=json.dumps({
			'type': 'match_found',
			'room': player2.room_id,
			'messagge': '¡Mach Found!',
			'color':  'palegreen'
		}))
		await asyncio.sleep(1)
		await self.countdown(player1, player2)

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
		movement_direction = data.get('action', 0)
		is_player1 = room['player1'].user_id == self.user_id
		#print(f"amos pulsao tecla {movement_direction}")
		
		if movement_direction == 'upOn':
			if is_player1:
				room['game_state']['player1up'] = True
			else:
				room['game_state']['player2up'] = True
		elif movement_direction == 'downOn':
			if is_player1:
				room['game_state']['player1down'] = True
			else:
				room['game_state']['player2down'] = True
		elif movement_direction == 'upOff':
			if is_player1:
				room['game_state']['player1up'] = False
			else:
				room['game_state']['player2up'] = False
		elif movement_direction == 'downOff':
			if is_player1:
				room['game_state']['player1down'] = False
			else:
				room['game_state']['player2down'] = False
		else:
			await self.send(text_data=json.dumps({
				'type': 'error',
				'message': "Bad request, parameter 'direction' is mandatory."
			}))
			return
		#await self.send_game_state_update(room)

	async def send_game_state_update(self, room):

		await room['player1'].send(text_data=json.dumps({
			'type': 'game_state_update',
			'player1Y': room['game_state']['player1Y'],
			'player2Y': room['game_state']['player2Y'],
			'ballX': room['game_state']['ball']['position']['x'],
			'ballY': room['game_state']['ball']['position']['y'],
		}))
		await room['player2'].send(text_data=json.dumps({
			'type': 'game_state_update',
			'player1Y': room['game_state']['player1Y'],
			'player2Y': room['game_state']['player2Y'],
			'ballX': room['game_state']['ball']['position']['x'],
			'ballY': room['game_state']['ball']['position']['y'],
		}))

	async def update_ball(self, room_id):
		room = active_rooms.get(room_id, [])
		"""
		De momento el bucle es infinito pero hay que gestionar
		que acabe cuando la partida acaba o algún jugador se desconecta
		"""

		incrementedSpeed = 0
		angleVariation = 1
		speedIncrement = 0.5
		playing =True
		ball_speed = room['game_state']['ball']['speed']
		ball_position = room['game_state']['ball']['position']
		speedX = room['game_state']['ball']['speed']['x']
		speedY = room['game_state']['ball']['speed']['y']
		totalSpeed = room['game_state']['ball']['speed']['x'] + room['game_state']['ball']['speed']['y']

		#print (f"player1: {room['player1.user_id']['player1Y']}  player2: {room['player2']}")

		while playing:
			#print(f"p1: {room['game_state']['Player1Points']}    p2: {room['game_state']['Player1Points']}")

			ball_position['x'] += speedX
			ball_position['y'] += speedY

			if ball_position["y"] >= 390 or ball_position["y"] <= 10:
				speedY *= -1
				#print("ARRIBA-ABAJO")

#----------------LEFT COLISION----------------------------------------------------------------------------

			if ball_position["x"] <= 10:
				if (ball_position["y"] >= room['game_state']['player1Y'] and 
				ball_position["y"] < room['game_state']['player1Y'] + 33.3):
					speedX *= -1
					#print(f"arriba   x = {speedX:.1f}   y = {speedY:.1f}")
					if speedY <= 0:
						if abs(speedX) > abs(speedY):
							speedX -= angleVariation
							speedY -= angleVariation
					else:
						speedY -= angleVariation
						speedX = totalSpeed - abs(speedY)
					#print(f"LEFT ARRIBA  {speedY}")
				elif (ball_position["y"] >= room['game_state']['player1Y'] + 33.3 and 
				ball_position["y"] < room['game_state']['player1Y'] + 66.6):
					speedX *= -1
					#print(f"LEFT MEDIO  {speedY}")
				elif (ball_position["y"] >= room['game_state']['player1Y'] + 66.6 and 
				ball_position["y"] < room['game_state']['player1Y'] + 100):
					speedX *= -1
					#print(f"abajo   x = {speedX:.1f}   y = {speedY:.1f}")
					if speedY >= 0:
						if abs(speedX) > abs(speedY):
							speedX -= angleVariation
							speedY += angleVariation
					else:
						speedY += angleVariation
						speedX = totalSpeed - abs(speedY)
					#print(f"LEFT ABAJO  {speedY}")
			
				else:
					await self.marker_update(room, 2)
					incrementedSpeed = 0
					speedX = room['game_state']['ball']['speed']['x']
					speedY = room['game_state']['ball']['speed']['y']
					#print(f"p1: {room['game_state']['Player1Points']}    p2: {room['game_state']['Player1Points']}")
					if room['game_state']['Player1Points'] == 3 or room['game_state']['Player2Points'] == 3: #fin de partida endgame
						playing = False
						if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
							await room['player1'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': '¡You WIN!',
								'color':  'palegreen',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
							await room['player2'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': 'You LOSE \n(you piece of shit)',
								'color':  'red',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
						else:
							await room['player1'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': 'You LOSE \n(you piece of shit)',
								'color':  'red',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
							await room['player2'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': 'You WIN',
								'color':  'palegreen',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
					else:
						await room['player1'].send(text_data=json.dumps({
							'type': 'update',
							'player1Points': room['game_state']['Player1Points'],
							'player2Points': room['game_state']['Player2Points'],
						}))
						await room['player2'].send(text_data=json.dumps({
							'type': 'update',
							'player1Points': room['game_state']['Player1Points'],
							'player2Points': room['game_state']['Player2Points'],
						}))
						await self.countdown(room['player1'], room['player2'])
						continue

				
				ball_position["x"] = 11
				speedX += speedIncrement
				if speedY <= 0:
					speedY -= speedIncrement
				else:
					speedY += speedIncrement
				incrementedSpeed += speedIncrement 
			
			
#----------------RIGHT COLISION----------------------------------------------------------------------------

			if ball_position["x"] >= 590:
				if (ball_position["y"] >= room['game_state']['player2Y'] and 
				ball_position["y"] < room['game_state']['player2Y'] + 33.3):
					speedX *= -1
					#print(f"arriba   x = {speedX:.1f}   y = {speedY:.1f}")
					if speedY <= 0:
						if abs(speedX) > abs(speedY):
							speedX += angleVariation
							speedY -= angleVariation
					else:
						speedY -= angleVariation
						speedX = - totalSpeed + abs(speedY)
					#print(f"RIGHT ARRIBA  {speedY}")
				elif (ball_position["y"] >= room['game_state']['player2Y'] + 33.3 and 
				ball_position["y"] < room['game_state']['player2Y'] + 66.6):
					speedX *= -1
					#print(f"RIGHT MEDIO  {speedY}")
				elif (ball_position["y"] >= room['game_state']['player2Y'] + 66.6 and 
				ball_position["y"] < room['game_state']['player2Y'] + 100):
					speedX *= -1
					#print(f"abajo   x = {speedX:.1f}   y = {speedY:.1f}")
					if speedY >= 0:
						if abs(speedX) > abs(speedY):
							speedX += angleVariation
							speedY += angleVariation
					else:
						speedY += angleVariation
						speedX = - totalSpeed + abs(speedY)
					#print(f"RIGHT ABAJO  {speedY}")
			
				else:
					await self.marker_update(room, 1)
					incrementedSpeed = 0
					speedX = -room['game_state']['ball']['speed']['x']
					speedY = room['game_state']['ball']['speed']['y']
					
					if room['game_state']['Player1Points'] == 3 or room['game_state']['Player2Points'] == 3: #fin de partida endgame
						playing = False
						if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
							await room['player1'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': '¡You WIN!',
								'color':  'palegreen',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
							await room['player2'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': 'You LOSE \n(you piece of shit)',
								'color':  'red',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
						else:
							await room['player1'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': 'You LOSE \n(you piece of shit)',
								'color':  'red',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
							await room['player2'].send(text_data=json.dumps({
								'type': 'finish',
								'messagge': 'You WIN',
								'color':  'palegreen',
								'player1Points': room['game_state']['Player1Points'],
								'player2Points': room['game_state']['Player2Points'],
							}))
					else:
						await room['player1'].send(text_data=json.dumps({
							'type': 'update',
							'player1Points': room['game_state']['Player1Points'],
							'player2Points': room['game_state']['Player2Points'],
						}))
						await room['player2'].send(text_data=json.dumps({
							'type': 'update',
							'player1Points': room['game_state']['Player1Points'],
							'player2Points': room['game_state']['Player2Points'],
						}))
						await self.countdown(room['player1'], room['player2'])
						continue

				
				ball_position["x"] = 589
				speedX -= speedIncrement
				if speedY <= 0:
					speedY -= speedIncrement
				else:
					speedY += speedIncrement
				incrementedSpeed += speedIncrement 

			# Movimiento de las palas
			if room['game_state']['player1up'] and room['game_state']['player1Y'] > 0:
				room['game_state']['player1Y'] -= room['game_state']['paddleSpeed']
			if room['game_state']['player1down'] and room['game_state']['player1Y'] < 300:
				room['game_state']['player1Y'] += room['game_state']['paddleSpeed']
			if room['game_state']['player2up'] and room['game_state']['player2Y'] > 0:
				room['game_state']['player2Y'] -= room['game_state']['paddleSpeed']
			if room['game_state']['player2down'] and room['game_state']['player2Y'] < 300:
				room['game_state']['player2Y'] += room['game_state']['paddleSpeed']

			totalSpeed = abs(speedX) + abs(speedY)
			#print(f"V total = {totalSpeed}")

			await self.send_game_state_update(room)
			await asyncio.sleep(0.030)  #  0.002Actualizar la pelota cada x ms


	async def marker_update(self, room, player):
		if player == 1:
			room['game_state']['Player1Points'] += 1
		else:
			room['game_state']['Player2Points'] += 1

		room['game_state']['ball']['position']['x'] = 300
		room['game_state']['ball']['position']['y'] = 200
		
		room['game_state']['player1Y'] = 150
		room['game_state']['player2Y'] = 150
