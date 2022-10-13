import click
import socket
from contextlib import contextmanager


@contextmanager
def create_socket(adrr):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(adrr)

    yield client_socket


def read_all(conn, buffer=16):
    data = bytearray()

    while True:
        chunk = conn.recv(buffer)
        if not chunk:
            break
        data += chunk

    if data:
        return bytes(data).decode()


def handle_connection(adrr):
    command = input("cmd> ")
    with create_socket(adrr) as client_socket:
        try:
            # Отправка данных
            print(f'Отправлено: {command}')
            client_socket.sendall(command.encode('utf-8'))

            # Ожидание ответа
            data = read_all(client_socket)
            if data:
                print(f'Получено: {data}')

        finally:
            print('Закрываем сокет')
            client_socket.close()


@click.command()
@click.option('--host', default='localhost', help='server host, localhost by default')
@click.option('--port', default=10000, help='server port, 10000 by default')
def main(host, port):
    adrr = (host, port)
    handle_connection(adrr)


if __name__=='__main__':
    main()
