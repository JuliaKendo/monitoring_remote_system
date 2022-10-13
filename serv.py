import click
import socket
import subprocess
from contextlib import suppress, contextmanager


@contextmanager
def create_socket(adrr):
    serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    serv_socket.bind(adrr)
    serv_socket.listen(1)

    yield serv_socket

    print('Закрываем сокет')
    serv_socket.close()


def read_all(conn, buffer=16):
    data = bytearray()
    with suppress(BlockingIOError):
        while True:
            data += conn.recv(buffer)
    
    if data:
        return bytes(data).decode()


def handle_command(command):
    proc = subprocess.Popen(
        command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    return proc.communicate()


def handle_connection(adrr):
    with create_socket(adrr) as serv_socket:
        print('Старт сервера на {}, порт {}'.format(*adrr))
        while True:
            print('Ожидание соединения')
            conn, address = serv_socket.accept()
            print(f'Подключено к {address}')
            conn.settimeout(0) # Запускаем соединение в неблокируещем режиме

            try:
                print('Обработка данных...')
                command = read_all(conn)
                if not command:
                    continue
                
                if command == 'exit':
                    raise SystemExit

                print(f'Получено: {command}')
                result, err = handle_command(command)
                
                print(f'Отправка обратно клиенту {result.decode()}')
                conn.sendall(result)

            except ConnectionResetError as err:
                print(f'Отправка обратно клиенту {err}')
                conn.sendall(err.encode('utf-8'))

            finally:
                print('Закрываем соединение')
                conn.close()


@click.command()
@click.option('--host', default='localhost', help='server host, localhost by default')
@click.option('--port', default=10000, help='server port, 10000 by default')
def main(host, port):
    adrr = (host, port)
    handle_connection(adrr)


if __name__=='__main__':
    main()
