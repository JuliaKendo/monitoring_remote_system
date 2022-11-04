import logging
import telegram


class NotificationLogHandler(logging.Handler):

    def __init__(self, token, chat_id):
        super().__init__()
        self.token = token
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        if log_entry:
            bot = telegram.Bot(token=self.token)
            bot.sendMessage(chat_id=self.chat_id, text=log_entry)


def initialize_logger(logger, log_token, chat_id):
    format='%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
    handler = NotificationLogHandler(log_token, chat_id)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)