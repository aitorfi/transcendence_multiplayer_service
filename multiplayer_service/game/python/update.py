async def marker_update(room, player):
    if player == 1:
        room['game_state']['Player1Points'] += 1
    else:
        room['game_state']['Player2Points'] += 1

    room['game_state']['ball']['position']['x'] = 300
    room['game_state']['ball']['position']['y'] = 200
    
    room['game_state']['player1Y'] = 150
    room['game_state']['player2Y'] = 150
