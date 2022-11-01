import asyncio
import datetime
import logging
import functools
import json
import click
import random
import subprocess
import websockets

from websockets.exceptions import ConnectionClosedOK


logger = logging.getLogger('monitoring_remote_server')
logging.basicConfig(
    filename='mrs.log',
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
)


def handle_connection(func):

    @functools.wraps(func)
    async def func_wrapped(url, **kwargs):
        connection_attempts = 0
        while True:
            wait_connection = 60 if connection_attempts < 3 else 3600
            try:
                async with websockets.connect(url) as ws:
                    connection_attempts = 0
                    await check_connection(ws)
                    await func(ws, kwargs)
            except (ConnectionRefusedError, ConnectionClosedOK) as err:
                logger.error(f'error connection: {err}')
                await asyncio.sleep(wait_connection)
                connection_attempts += 1
                continue
            except Exception as err: # noqa
                logger.error(f'error connection to server: {err}')
                await asyncio.sleep(wait_connection)
                connection_attempts += 1
                continue

    return func_wrapped



async def check_connection(ws):
    await ws.send(
        json.dumps({
            'source': 'client', 'message': 'client connected'
        })
    )
    logger.debug('client connected')


def handle_command(command):
    logger.debug(f'run command: {command}')
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
            
            if err:
                logger.error(f'error run command: {err.decode(encoding=params["encoding"])}')
                continue
            
            try:
                decode_result = int(result.decode(encoding=params['encoding']))
            except Exception as err:
                logger.error(f'error decode or convert result: {err}')
                continue
            
            if decode_result >= params['min_free_space']:
                continue

            logger.debug(f'result command: {decode_result}')
            await ws.send(
                json.dumps({
                    'source': 'client',
                    'message': f'Warning, {params.get("id", "your")} computer gonna be running out of disk space. Left {decode_result} byte free space'
                })
            )


@click.command()
@click.option('--host', default='localhost', help='server host, localhost by default')
@click.option('--port', default=10000, help='server port, 10000 by default')
@click.option('--encoding', default="utf-8", help='encoding')
@click.option('--mfs', default=100, help='min free space in byte')
@click.option('--id', help='computer name')
def main(host, port, encoding, mfs, id):
    asyncio.run(client(
        f'ws://{host}:{port}/ws/{int(datetime.datetime.now().timestamp())}{random.randint(10, 99)}',
        encoding = encoding,
        min_free_space = mfs,
        id = id
    ))


if __name__ == "__main__":
    main()
