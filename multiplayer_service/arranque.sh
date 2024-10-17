#pip install channels daphne

python3 -m daphne -b 0.0.0.0 -p 50002 multiplayer_service.asgi:application 