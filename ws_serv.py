import asyncio
import json
import click
import logging

from environs import Env
from quart import Quart, render_template, websocket
from collections import defaultdict

from logger_lib import initialize_logger


env = Env()
env.read_env()

logger = logging.getLogger('monitoring_remote_server')
initialize_logger(logger, env.str('TG_LOG_TOKEN'), env.str('TG_CHAT_ID'))

clients = defaultdict()
app = Quart(__name__)


def get_receiver(source):
    receiver = ''
    if source == 'front':
        receiver = 'client'
    elif source == 'client':
        receiver = 'front'
    return receiver
        

async def receive_message(ws, queue):
    while True:
        received_data = await ws.receive()
        decoded_data = json.loads(received_data)
        unique_ids = [key for key, item in clients.items() if item['ws'] == ws]
        for unique_id in unique_ids:
            clients[unique_id]['type'] = decoded_data['source']
        await queue.put({
            'receiver': get_receiver(decoded_data['source']),
            'message': decoded_data['message']
        })
        logger.debug(
            f'get message from {unique_ids if unique_ids else "empty id"}: {decoded_data["message"]}'
        )


async def send_message(unique_id, queue):
    while True:
        received_data = await queue.get()
        queue.task_done()
        for key, client in clients.items():
            if key == unique_id:
                continue
            if client['type'] != received_data['receiver']:
                continue
            await client['ws'].send(received_data['message'])
            logger.debug(f'send message to {key if key else "empty id"}: {received_data["message"]}')


@app.route("/")
async def index():
    return await render_template("index.html")


@app.websocket("/ws/<unique_id>")
async def ws(unique_id):
    queue = asyncio.Queue()
    tasks = []
    try:
        clients[unique_id] = {'ws': websocket._get_current_object(), 'type': ''}
        tasks.append(
            asyncio.create_task(receive_message(websocket, queue))
        )
        tasks.append(
            asyncio.create_task(send_message(unique_id, queue))
        )
        await asyncio.gather(*tasks)
        await queue.join()

    finally:
        del clients[unique_id]


@click.command()
@click.option('--host', default='localhost', help='server host, localhost by default')
@click.option('--port', default=10000, help='server port, 10000 by default')
def main(host, port):
    logger.debug('Server start')
    loop = asyncio.get_event_loop()
    app.run(host=host, port=port, debug=1, loop=loop)


if __name__ == "__main__":
    main()
    