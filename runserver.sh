#!/bin/bash

cd multiplayer_service
python3 -m daphne -p 50002 multiplayer_service.asgi:application