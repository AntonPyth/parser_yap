# utils.py
import logging

# Импорт базового класса ошибок библиотеки request.
from requests import RequestException

# Перехват ошибки RequestException.
def get_response(session, url):
    try:
        response = session.get(url) 
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )