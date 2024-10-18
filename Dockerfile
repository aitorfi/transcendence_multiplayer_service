FROM python:3

WORKDIR /usr/src/app

RUN pip install Django channels daphne aiohttp jwt

COPY ./runserver.sh /usr/bin/
RUN chmod +x /usr/bin/runserver.sh

EXPOSE 8080

CMD [ "/usr/bin/runserver.sh" ]