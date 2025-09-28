# test.py
import re
from urllib.parse import urljoin
from pathlib import Path

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, WHATS_NEW_URL, DOWNLOADS_URL
from configs import configure_argument_parser

def whats_new(session):
    # Вместо константы WHATS_NEW_URL, используйте переменную whats_new_url.
    # Привязка к MAIN_DOC_URL через urljoin.
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    response = session.get(whats_new_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')

    main_section = soup.find('section', attrs={'id': 'what-s-new-in-python'})
    if main_section is None:
        raise RuntimeError('Раздел "What\'s New" не найден на странице')

    toctree = main_section.find('div', attrs={'class': 'toctree-wrapper'})
    if toctree is None:
        raise RuntimeError('Список версий в "What\'s New" не найден')

    sections_by_python = toctree.find_all('li', attrs={'class': 'toctree-l1'})

    results = []
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        if version_a_tag is None or 'href' not in version_a_tag.attrs:
            continue
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        # Запрос страницы конкретной версии What's New
        v_resp = session.get(version_link)
        v_resp.encoding = 'utf-8'
        v_soup = BeautifulSoup(v_resp.text, 'lxml')

        h1 = v_soup.find('h1')
        dl = v_soup.find('dl')
        h1_text = h1.text.strip() if h1 else ''
        dl_text = dl.text.replace('\n', ' ').strip() if dl else ''

        results.append((version_link, h1_text, dl_text))

    # Вывод результатов, как в исходнике
    for row in results:
        print(*row)

    return results


def latest_versions(session):
    response = session.get(MAIN_DOC_URL)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')

    sidebar = soup.find('div', {'class': 'sphinxsidebarwrapper'})
    if sidebar is None:
        raise RuntimeError('Sidebar not found')

    ul_tags = sidebar.find_all('ul')

    a_tags = None
    for ul in ul_tags:
        if 'All versions' in ul.get_text():
            a_tags = ul.find_all('a')
            break
    if not a_tags:
        raise RuntimeError('Ничего не нашлось')

    results = []
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag.get('href', '')
        # Приводим ссылку к абсолютной, чтобы было удобно использовать вне контекста
        absolute_link = urljoin(MAIN_DOC_URL, link)
        text_match = re.search(pattern, a_tag.get_text())
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.get_text(), ''
        results.append((absolute_link, version, status))

    for row in results:
        print(*row)

    return results


def download(session):
    # Вместо константы DOWNLOADS_URL, используйте переменную downloads_url.
    # Привязка к MAIN_DOC_URL через urljoin.
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    response = session.get(downloads_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')

    main_tag = soup.find('div', {'role': 'main'})
    if main_tag is None:
        raise RuntimeError('Главный блок (role=main) не найден на странице загрузок')

    table_tag = main_tag.find('table', {'class': 'docutils'})
    if table_tag is None:
        raise RuntimeError('Таблица с загрузками не найдена')

    pdf_a4_tag = table_tag.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    if pdf_a4_tag is None:
        raise RuntimeError('Ссылка на pdf-a4.zip не найдена')

    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)

    filename = archive_url.rstrip('/').split('/')[-1]
    print(f'Ссылка на файл: {archive_url}')

    downloads_dir = Path(BASE_DIR) / 'downloads'
    downloads_dir.mkdir(exist_ok=True)

    archive_path = downloads_dir / filename

    # Скачивание архива
    file_resp = session.get(archive_url)
    file_resp.raise_for_status()
    with open(archive_path, 'wb') as f:
        f.write(file_resp.content)

    return archive_path

MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
}

def main():    
    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()

    session = requests_cache.CachedSession()
    # Если был передан ключ '--clear-cache', то args.clear_cache == True.
    if args.clear_cache:
        # Очистка кеша.
        session.cache.clear()

    parser_mode = args.mode
    # С вызовом функции передаётся и сессия.
    MODE_TO_FUNCTION[parser_mode](session)

if __name__ == '__main__':
    main()
