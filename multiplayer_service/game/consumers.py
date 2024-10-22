import json
import time
import asyncio
import aiohttp # para hacer solicitudes http a math history
import jwt
import os
import uuid
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer

from django.conf import settings
from datetime import datetime


# Diccionario global para mantener a los jugadores esperando
waiting_players = []

waiting_semifinal_players = []

waiting_final_players = []

# Diccionario para almacenar las salas activas (por simplicidad, puede ser reemplazado por una base de datos)
active_rooms = {}

tournaments = {}
active_connections = {} 

id = 1





    

class GameMatchmakingConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # crea una instancia de PlayerConsumer:


    def print_object_attributes(obj):
        attributes = {key: value for key, value in vars(obj).items() if not key.startswith('__')}
        print(f"Atributos de {type(obj).__name__}:")
        for key, value in attributes.items():
            print(f"  {key}: {value}")



    def decode_jwt_token(self, token):
        try:
            # Decodifica el token usando la clave secreta de Django
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            print("El token ha expirado")
            return None
        except jwt.InvalidTokenError:
            print("El token ha expirado")
            return None



    async def send_game_result(self, room):
   
        url = "http://localhost:60000/api/matches2/game-results/"  # Reemplaza con la URL correcta
        print(f"Grabando resultadods")
        winner = 0
        if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
            winner =  room['game_state']['player1_id']
        else:
            winner =  room['game_state']['player2_id']
    
        data = {
            "player1_id": room['game_state']['player1_id'],
            "player2_id": room['game_state']['player2_id'],
            "player1_display_name": room['game_state']['player1_display_name'],
            "player2_display_name": room['game_state']['player2_display_name'],
            "player1_score": room['game_state']['Player1Points'],
            "player2_score":  room['game_state']['Player2Points'],
            "match_type": room['game_state']['match_type'],
            "winner_id": winner,
            "tournament_id": room['game_state']['tournament_id'],
        }
        print(f"El juego sigue aqui: {data}")
        print("Enviando conexion para enviar datos.")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    print("Resultado enviado exitosamente")
                    if room['game_state']['match_type'] == 'FINAL':
                        await self.end_tournament(room['game_state']['tournament_id'], winner)
                else:
                    print(f"Error al enviar resultado: {response.status}")


    

    async def register_tournament(self, start_date=None, winner_id=0):
        url = "http://localhost:60000/api/matches2/register-tournament/"

        if start_date is None:
            start_date = datetime.now()

        data = {
            "start_date": start_date.isoformat(),
            "winner_id": winner_id
        }

        print(f"Registrando torneo con datos: {data}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('status') == 'success':
                            print(f"Torneo registrado exitosamente. ID: {result.get('tournament_id')}")
                            return result.get('tournament_id')
                        else:
                            print(f"Error al registrar torneo: {result.get('message')}")
                            return None
                    else:
                        print(f"Error al registrar torneo. Código de estado: {response.status}")
                        return None
            except aiohttp.ClientError as e:
                print(f"Error de conexión al registrar torneo: {str(e)}")
                return None
            



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

        payload = self.decode_jwt_token(data['token'])
        print(f"Token decodificado: {payload}")

        self.user_id = payload.get('user_id')
        self.display_name = payload.get('display_name')
        self.game_type = data.get('game_type')
        self.game_id = data.get('game_id') 


        print(f"Cliente autenticado - ID: {self.user_id}, Nombre: {self.display_name}, ")

        global id
   
        self.print_object_attributes()
        id = self.user_id
        if self.user_id:
                      
            if self.game_type == 'SEMIFINAL':
                waiting_semifinal_players.append(self)
            elif self.game_type == 'FINAL':
                waiting_final_players.append(self)
            else: 
                waiting_players.append(self)
            await self.match_players()
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': "Bad request, parameter 'user_id' is mandatory"
            }))



    def get_player_connection(self, player_id):
        for room in active_rooms.values():
            if room['player1'].user_id == player_id:
                return room['player1']
            if room['player2'].user_id == player_id:
                return room['player2']
        return None


    async def check_semifinals_completion(self, tournament_id):
        try:
            while True:
                print(f"Verificando estado del torneo {tournament_id}")
                if await self.are_semifinals_completed(tournament_id):
                    print(f"Semifinales completadas para el torneo {tournament_id}")
                    await self.prepare_final(tournament_id)
                    break
                await asyncio.sleep(5)  # Verifica cada 5 segundos
        except Exception as e:
            print(f"Error en check_semifinals_completion: {str(e)}")
            import traceback
            traceback.print_exc()
  
    async def are_semifinals_completed(self, tournament_id):
        if tournaments[tournament_id]['room1'] != 0 and tournaments[tournament_id]['room2'] != 0:
           return 1
        return 0



    """     async def are_semifinals_completed(self, tournament_id):
            url = f"http://localhost:60000/api/matches2/tournament-status/{tournament_id}/"
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            completed = data.get('semifinals_completed', False)
                            print(f"Estado de semifinales para torneo {tournament_id}: {'Completadas' if completed else 'No completadas'}")
                            return completed
                        else:
                            print(f"Error al verificar el estado del torneo. Código de estado: {response.status}")
                            return False
                except aiohttp.ClientError as e:
                    print(f"Error de conexión al verificar el estado del torneo: {str(e)}")
                    return False
    """

    async def prepare_final(self, tournament_id):
        try:
            winners = await self.get_semifinal_winners(tournament_id)
            print(f"Ganadores de semifinales para torneo {tournament_id}: {winners}")
            
            if len(winners) == 2:
                print("Preparando la final...")
                # Guarda los ganadores y el ID del torneo para usarlos más tarde
                self.final_players = winners
                self.final_tournament_id = tournament_id
                
                # Iniciar la final directamente
                await self.start_final()
            else:
                print(f"Error: No se encontraron 2 ganadores para el torneo {tournament_id}. Ganadores encontrados: {len(winners)}")
        except Exception as e:
            print(f"Error en prepare_final: {str(e)}")
            import traceback
            traceback.print_exc()


    def create_player_object(self, user_id, display_name, tournament_id):
        class Player:
            def __init__(self, user_id, display_name, tournament_id):
                self.user_id = user_id
                self.display_name = display_name
                self.tournament_id = tournament_id
                self.send = self.dummy_send  # Añade un método send dummy
                self.room_id = None
            async def dummy_send(self, text_data):
                print(f"Enviando datos a {self.display_name}: {text_data}")

        return Player(user_id, display_name, tournament_id)


    async def get_semifinal_winners(self, tournament_id):
        url = f"http://localhost:60000/api/matches2/semifinal-winners/{tournament_id}/"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        winners = data.get('winners', [])
                        # Buscar las conexiones de los ganadores
                        winner_connections = []
                        for winner in winners:
                            if isinstance(winner, dict):
                                user_id = winner.get('user_id')
                            elif isinstance(winner, int):
                                user_id = winner
                            else:
                                print(f"Formato de ganador inesperado: {winner}")
                                continue
                            
                            connection = self.get_player_connection(user_id)
                            if connection:
                                winner_connections.append(connection)
                            else:
                                print(f"No se encontró conexión para el jugador {user_id}")
                        return winner_connections
                    else:
                        print(f"Error al obtener los ganadores de las semifinales. Código de estado: {response.status}")
                        return []
            except aiohttp.ClientError as e:
                print(f"Error de conexión al obtener los ganadores de las semifinales: {str(e)}")
                return []


    async def start_final(self):
        if not hasattr(self, 'final_players') or len(self.final_players) != 2:
            print("Error: No hay jugadores disponibles para la final")
            return

        player1 = self.final_players[0]
        player2 = self.final_players[1]

        self.player1_user_id = player1.user_id
        self.player1_display_name = player1.display_name
        self.player2_user_id = player2.user_id
        self.player2_display_name = player2.display_name

        print(f"Iniciando la final:")
        print(f"Player 1 - ID: {self.player1_user_id}, Nombre: {self.player1_display_name}")
        print(f"Player 2 - ID: {self.player2_user_id}, Nombre: {self.player2_display_name}")

        try:
            await self.init_new_game(player1, player2, 'FINAL', self.final_tournament_id)
            print("Juego final inicializado")
            await self.notify_match_found(player1, player2)
            print("Notificación de emparejamiento enviada")
            asyncio.create_task(self.update_ball(f"room_{self.player1_user_id}_{self.player2_user_id}"))
            print("Tarea de actualización de bola creada")
            await self.notify_start_game(player1, player2)
            print("Notificación de inicio de juego enviada")
        except Exception as e:
            print(f"Error al iniciar la final: {str(e)}")
            import traceback
            traceback.print_exc()



    async def end_tournament(self, tournament_id, winner_id):
        
        print("Game finished")
        
        """         url = f"http://localhost:60000/api/matches2/end-tournament/{tournament_id}/"
                data = {
                    "winner_id": winner_id
                }
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(url, json=data) as response:
                            if response.status == 200:
                                print(f"Torneo {tournament_id} finalizado. Ganador: {winner_id}")
                            else:
                                print(f"Error al finalizar el torneo. Código de estado: {response.status}")
                    except aiohttp.ClientError as e:
                        print(f"Error de conexión al finalizar el torneo: {str(e)}")
         """




    async def match_players(self):
        """Intenta emparejar jugadores en la lista de espera."""
        if len(waiting_players) >= 2:  # Necesitamos al menos dos jugadores para emparejar
            # Emparejar a los dos primeros jugadores
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)

            self.player1_user_id = player1.user_id
            self.player1_display_name = player1.display_name
            
            self.player2_user_id = player2.user_id
            self.player2_display_name = player2.display_name

            print(f"Emparejando jugadores:")
            print(f"Player 1 - ID: {player1.user_id}, Nombre: {player1.display_name}")
            print(f"Player 2 - ID: {player2.user_id}, Nombre: {player2.display_name}")
            print(f"Emparejando type:{self.game_type}")
            print(f"Emparejando id:{self.game_id}")

            await self.init_new_game(player1, player2, 'INDIVIDUAL', 0)
            await self.notify_match_found(player1, player2)
            #await asyncio.sleep(1)
            asyncio.create_task(self.update_ball(self.room_id))

        elif len(waiting_semifinal_players) >= 4:
            player1 = waiting_semifinal_players.pop(0)
            player2 = waiting_semifinal_players.pop(0)
      
            self.player1_user_id = player1.user_id
            self.player1_display_name = player1.display_name
            self.player2_user_id = player2.user_id
            self.player2_display_name = player2.display_name
            tournament_uuid = uuid.uuid4()  # Primero generamos el UUID
            id_torneo = int(str(uuid.uuid4().hex)[:7], 16) 
            tournaments[id_torneo] = {'room1': 0, 'room2': 0, 'room1display': "", 'room2display': ""}
            print(f"Torneo Creado {id_torneo}")
            print(f"Emparejando jugadores Grupo A:")
            print(f"Player 1 - ID: {player1.user_id}, Nombre: {player1.display_name}")
            print(f"Player 2 - ID: {player2.user_id}, Nombre: {player2.display_name}")

            await self.init_new_game(player1, player2, 'SEMIFINAL', id_torneo)
            await self.notify_match_found(player1, player2)
            #await asyncio.sleep(1)
            asyncio.create_task(self.update_ball(f"room_{player1.user_id}_{player2.user_id}"))
            await self.notify_start_game(player1, player2)
 
            player1 = waiting_semifinal_players.pop(0)
            player2 = waiting_semifinal_players.pop(0)
      
            self.player1_user_id = player1.user_id
            self.player1_display_name = player1.display_name
            self.player2_user_id = player2.user_id
            self.player2_display_name = player2.display_name

            print(f"Emparejando jugadores Grupo B:")
            print(f"Player 1 - ID: {player1.user_id}, Nombre: {player1.display_name}")
            print(f"Player 2 - ID: {player2.user_id}, Nombre: {player2.display_name}")

            await self.init_new_game(player1, player2, 'SEMIFINAL', id_torneo)
            await self.notify_match_found(player1, player2)
            #await asyncio.sleep(1)
            asyncio.create_task(self.update_ball(f"room_{player1.user_id}_{player2.user_id}"))
            await self.notify_start_game(player1, player2)
            asyncio.create_task(self.check_semifinals_completion(id_torneo))
            print(f"Tarea de verificación de semifinales iniciada para el torneo {id_torneo}")
        elif len(waiting_final_players) >= 2:
                await self.start_final()

    async def init_new_game(self, player1, player2, match_type, tournament_id):
        # Crear una nueva sala para la partida
        room_id = f"room_{player1.user_id}_{player2.user_id}"


        await  player1.send(text_data=json.dumps({
            'type': 'setName',
            'player1DisplayName' : self.player1_display_name,
            'player2DisplayName' : self.player2_display_name,
            'player1Id' : self.player1_user_id,
            'player2Id' : self.player2_user_id,
            
        }))
        await player2.send(text_data=json.dumps({
            'type': 'setName',
            'player1DisplayName' : self.player1_display_name,
            'player2DisplayName' : self.player2_display_name,
            'player1Id' : self.player1_user_id,
            'player2Id' : self.player2_user_id,            
            
        }))

        # active_rooms[room_id] = [player1, player2]
        active_rooms[room_id] = {
            'player1': player1,
            'player2': player2,
            'game_state': {
                'player1_id': self.player1_user_id,
                'player1_display_name': self.player1_display_name,                  
                'player2_id': self.player2_user_id,
                'player2_display_name': self.player2_display_name,   
                'match_type': match_type,
                'tournament_id': tournament_id,                
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
        print(f"Las notas empiezan aqui: {active_rooms[room_id]}")

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

    async def send_game_state_update(self, room, speedx, speedy):

        await room['player1'].send(text_data=json.dumps({
            'type': 'game_state_update',
            'player1Y': room['game_state']['player1Y'],
            'player2Y': room['game_state']['player2Y'],
            'ballX': room['game_state']['ball']['position']['x'],
            'ballY': room['game_state']['ball']['position']['y'],
            'speedX': speedx,
            'speedY': speedy,
            'time': time.time()
        }))
        await room['player2'].send(text_data=json.dumps({
            'type': 'game_state_update',
            'player1Y': room['game_state']['player1Y'],
            'player2Y': room['game_state']['player2Y'],
            'ballX': room['game_state']['ball']['position']['x'],
            'ballY': room['game_state']['ball']['position']['y'],
            'speedX': speedx,
            'speedY': speedy,
            'time': time.time()
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
                        if tournaments[room['game_state']['tournament_id']]['room1'] == 0:
                            if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
                                tournaments[room['game_state']['tournament_id']]['room1'] = room['game_state']['player1_id']
                                tournaments[room['game_state']['tournament_id']]['room1display'] = room['game_state']['player1_display_name']
                            else:
                                tournaments[room['game_state']['tournament_id']]['room1'] = room['game_state']['player2_id']
                                tournaments[room['game_state']['tournament_id']]['room1display'] = room['game_state']['player2_display_name']
                        # Si no, asignar a room2
                        else:
                            if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
                                tournaments[room['game_state']['tournament_id']]['room2'] = room['game_state']['player1_id']
                                tournaments[room['game_state']['tournament_id']]['room2display'] = room['game_state']['player1_display_name']

                            else:
                                tournaments[room['game_state']['tournament_id']]['room2'] = room['game_state']['player2_id']
                                tournaments[room['game_state']['tournament_id']]['room2display'] = room['game_state']['player2_display_name']

                        
                        await self.send_game_result(room)
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
                        if tournaments[room['game_state']['tournament_id']]['room1'] == 0:
                            if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
                                tournaments[room['game_state']['tournament_id']]['room1'] = room['game_state']['player1_id']
                                tournaments[room['game_state']['tournament_id']]['room1display'] = room['game_state']['player1_display_name']
                            else:
                                tournaments[room['game_state']['tournament_id']]['room1'] = room['game_state']['player2_id']
                                tournaments[room['game_state']['tournament_id']]['room1display'] = room['game_state']['player2_display_name']
                        # Si no, asignar a room2
                        else:
                            if room['game_state']['Player1Points'] > room['game_state']['Player2Points']:
                                tournaments[room['game_state']['tournament_id']]['room2'] = room['game_state']['player1_id']
                                tournaments[room['game_state']['tournament_id']]['room2display'] = room['game_state']['player1_display_name']

                            else:
                                tournaments[room['game_state']['tournament_id']]['room2'] = room['game_state']['player2_id']
                                tournaments[room['game_state']['tournament_id']]['room2display'] = room['game_state']['player2_display_name']                        
                        
                        await self.send_game_result(room)
                        print(f"Ganador: {'winner'}")
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

            await self.send_game_state_update(room, speedX, speedY)
            await asyncio.sleep(0.030)  #  0.030 .002Actualizar la pelota cada x ms


    async def marker_update(self, room, player):
        if player == 1:
            room['game_state']['Player1Points'] += 1
        else:
            room['game_state']['Player2Points'] += 1

        room['game_state']['ball']['position']['x'] = 300
        room['game_state']['ball']['position']['y'] = 200
        
        room['game_state']['player1Y'] = 150
        room['game_state']['player2Y'] = 150
