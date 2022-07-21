import requests, os, json, time, sys

import telegram
from dotenv import load_dotenv

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


def send_message(bot, message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        # logger.error(f'{error} occured: message not sent')
        pass
    else:
        # logger.info('Message successfully sent')
        pass


def get_api_answer(current_timestamp):
    timestamp = current_timestamp
    #  or int(time.time())
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
    except Exception as error:  # не понял какую ошибку тут ловить
        pass
        # logger.error(f'{error} occured: message not sent')
    else:
        return json.loads(response.text)


def check_response(response):
    try:
        if 'homeworks' not in response:
            raise exc.ApiResponseError()
    except (TypeError, exc.ApiResponseError) as error:
        # logger.error(f'{error} occured: API response invalid')
        pass
    else:
        return response.get('homeworks')


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        # logger.error(f'{error} occured: homework status not recognized')
        pass
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    try:
        if not PRACTICUM_TOKEN:
            raise exc.PrTokenNotFound()
        if not TELEGRAM_TOKEN:
            raise exc.TgTokenNotFound()
        if not TELEGRAM_CHAT_ID:
            raise exc.ChatIdNotFound()
    except (exc.PrTokenNotFound, exc.TgTokenNotFound, exc.ChatIdNotFound) as error:
        # logger.critical(f'{error} occured: environment variable not found')
        # print(type(error).__name__)
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    if check_tokens() != True:
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = int(time.time())
    current_timestamp = 0
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                # logger.debug('homeworks list empty')
                pass
            for i in range(len(homeworks)):
                message = parse_status(homeworks[i])
                send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
