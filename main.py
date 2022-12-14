import os
import asyncio
import json
import click
import re
import random
import functools
import logging

from environs import Env
from configparser import ConfigParser
from datetime import datetime, timedelta
from scheduler.asyncio import Scheduler

from logger_lib import initialize_logger
from mailing import send_email
from ws_client import handle_connection


env = Env()
env.read_env()

logger = logging.getLogger('monitoring_remote_server')
initialize_logger(logger, env.str('TG_LOG_TOKEN'), env.str('TG_CHAT_ID'))


async def mail_message(msg, to_addr, subject):
    if not re.search(r'client connected', msg):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, functools.partial(send_email, subject, to_addr, msg))
    

async def handle_messages(ws, msg):
    await ws.send(
        json.dumps({
            'source': 'front',
            'message': msg
        })
    )


@handle_connection
async def client(ws, params):

    commands = [cmd.replace('\n','').strip() for cmd in params['commands'].split(',')]
    if not commands:
        logger.error("There are no commands! Exiting!")
        raise SystemExit("There are no commands! Exiting!")

    schedule = Scheduler()
    for command in commands:
        if not command:
            continue
        schedule.cyclic(
            timedelta(seconds=int(params['waiting_time'])),
            functools.partial(handle_messages, ws, command)
        )

    while True:
        result = await ws.recv()
        if result:
            await mail_message(result, params['mailto'], params['subject'])
        await asyncio.sleep(1)


@click.command()
@click.option('--host', default='localhost', help='server host, localhost by default')
@click.option('--port', default=10000, help='server port, 10000 by default')
def main(host, port):

    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config.ini")
    
    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
    else:
        logger.error("Config not found! Exiting!")
        raise SystemExit("Config not found! Exiting!")

    asyncio.run(client(
        f'ws://{host}:{port}/ws/{int(datetime.now().timestamp())}{random.randint(10, 99)}',
        waiting_time =cfg.get("schedule", "waiting_time"),
        subject      =cfg.get("mail", "subject"),
        mailto       =cfg.get("mail", "mailto"),
        commands     =cfg.get("common", "commands")
    ))


if __name__ == "__main__":
    main()
