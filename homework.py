import os
import time
import sys
import logging
import json
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
import requests
import telegram

import exceptions as exc


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PR_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# Создаем логгер и определяем формат лога
logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(name)s - %(message)s'
)
# Создаем хэндлер для записи в файл уровня error и присваиваем логгеру
fl_handler = RotatingFileHandler('bot.log', maxBytes=50000000, backupCount=5)
fl_handler.setLevel(logging.ERROR)
fl_handler.setFormatter(formatter)
logger.addHandler(fl_handler)
# Создаем хэндлер для записи в stdout уровня debug и присваиваем логгеру
str_handler = logging.StreamHandler(stream=sys.stdout)
str_handler.setLevel(logging.DEBUG)
str_handler.setFormatter(formatter)
logger.addHandler(str_handler)


def send_message(bot, message):
    """
    Отправляет сообщение в чат телеграм.
    В случае возникновения любых ошибок
    ловит и записывает в лог.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Message successfully sent')
    except telegram.TelegramError as error:
        logger.error(f'{repr(error)} occured during sending', exc_info=True)


def get_api_answer(current_timestamp):
    """Опрашивает АПИ практикума и возвращает словарь.
    В случае возникновнеия
    ошибок выбрасывает эксепшн ConnetctionError.
    """
    timestamp = current_timestamp or int(time.time())
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
        if response.status_code != HTTPStatus.OK:
            raise exc.HttpResponseError('API response not 200')
        return response.json()
    except json.decoder.JSONDecodeError as e:
        raise exc.ConnetctionError(f'Praktikum API answer in not JSON: {e}')
    except requests.exceptions.RequestException as e:
        raise exc.ConnetctionError(f'Praktikum API connection error: {e}')


def check_response(response):
    """Проверяет корректность ответа АПИ и наличие ключа homeworks.
    Возвращает значение словаря по ключу homeworks.
    """
    if not isinstance(response, dict):
        raise TypeError('API response cant be resolved into dict')
    if 'homeworks' not in response:
        raise exc.ApiResponseError('API response dont contain homework info')
    if not isinstance(response['homeworks'], list):
        raise TypeError('homeworks is not list')
    return response.get('homeworks')


def parse_status(homework):
    """Проверяет наличие обновлений статуса проверки домашней работы.
    Если статус не известен выбрасывает эксепшен.
    """
    if 'homework_name' not in homework:
        raise KeyError('"Homework" dictionary do not contain homework')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Homework status not recognized')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие переменных окружения.
    В случае отсутствия выбрасывает соответствующий эксепшн.
    """
    tokens = (PRACTICUM_TOKEN,
              TELEGRAM_TOKEN,
              TELEGRAM_CHAT_ID)
    for token in tokens:
        if not token:
            logger.critical(f'{token} occured: environment variable not found')
            return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_error = 0
    while True:
        try:
            if not check_tokens():
                sys.exit()
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logger.debug('homeworks list empty')
            for work in homeworks:
                message = parse_status(work)
                send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            error_message = repr(error)
            logger.error(f'{error_message} occured')
            if error_message != last_error:
                send_message(bot, f'{error_message}')
                last_error = error_message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
