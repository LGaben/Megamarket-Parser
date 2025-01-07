import random
import json

import pandas as pd

from os import remove
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
# from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from time import sleep


baseURL = 'https://megamarket.ru'
target = input('Искать товары: ')
# print('''# 'Популярные': '0',
# # 'Сначала дешевле': '1',
# # 'Снадала дороже':'2',
# # 'Высокий рейтинг': '3',
# # 'Много отзывов': '4',
# # 'Новинки': '5',
# # 'Снижена цена': '6' ''')
# SORT = {
#     '0': 'Популярные',
#     '1': 'Сначала дешевле',
#     '2': 'Снадала дороже',
#     '3': 'Высокий рейтинг',
#     '4': 'Много отзывов',
#     '5': 'Новинки',
#     '6': 'Снижена цена'
# }
# SORT_KEY = input('Порядок сортировки (введите номер):')
# SORT_KEY = '0'
targetURL = baseURL + '''/catalog/page-{page}/?q=''' + target.replace(
                                            ' ', '%20')
MAX_PAGES = 0
# break если мы уже на максимольный доступной странице по запросу
DATA = []

def get_source_html(url: str, pages: int):
    # chrome_options = webdriver.ChromeOptions()
    firefox_options = FirefoxOptions()
    # driver = webdriver.Chrome(options=chrome_options)

    # данные аргументы позволяют использовать движок браузера без gui
    # chrome_options.add_argument("--headless=new")
    # firefox_options.add_argument("-headless")
    driver = webdriver.Firefox(options=firefox_options)
    br = True  # break if dont have pages. True - only 1 page.
    try:
        for page in range(1, pages+1):
            driver.get(url=url.format(page=str(page)))
            WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((
                    By.XPATH,
                    "//*[@class='select field opened sm' or @class='catalog-items-list__container']"
                ))
            )
            # input("Press Enter to continue...")
            with open('source-page.html', 'w', encoding='utf-8') as file:
                file.write(driver.page_source)
            br, MAX_PAGES = get_items(
                file_path='source-page.html')
            if br or MAX_PAGES == page:
                remove('source-page.html')
                print(MAX_PAGES, br)
                print('выход')
                break
            remove('source-page.html')
            sleep(random.randint(10, 35)/10)
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def get_items(file_path):
    with open(file_path, encoding='utf-8') as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    if soup.find('div', class_='catalog-listing-not-found-regular'):
        print('''\033[31m[INFO] Мы это не нашли.
        Попробуйте изменить запрос
        или проверьте выбранный регион.''')
        return True, 0
    items_divs = soup.find('div', class_='catalog-items-list__container')
    items = items_divs.find_all('div', class_='ddl_product')
    for item in items:
        if 'catalog-item-regular-desktop_out-of-stock' not in item.attrs['class']:
            item_link = item.find('a', class_='catalog-item-image-block__image')
            img = item_link.find('img').get('src')
            item_link = item_link.get('href')
            item_block = item.find('div', class_='catalog-item-regular-desktop__main-info')
            name = ' '.join(item_block.find('a').text.split())
            store = ' '.join(item_block.find('span', class_='merchant-info__name').text.split())
            price = ''.join(item.find('div', class_='catalog-item-regular-desktop__price').text.split())
            if bonus_percent := item.find('span', class_='bonus-percent'):
                bonus_percent = bonus_percent.text
            if bonus_amount := item.find('span', class_='bonus-amount'):
                bonus_amount = bonus_amount.text
            item_param = {
                'Название': name,
                'Ссылка на товар': 'https://megamarket.ru' + item_link,
                'Картинка': img,
                'Цена': price,
                'Продавец': store,
                'Процнет бонуса': bonus_percent,
                'Кол-во бонусов': bonus_amount
            }
            if additional_info := item.find_all('div', class_='item-details-item'):
                for info in additional_info:
                    info_detail = info.find('span').text.split(': ')
                    item_param[info_detail[0]] = info_detail[1]
            DATA.append(item_param)
    try:
        if MAX_PAGES == 0:
            page_soup = soup.find('nav', class_='pager catalog-items-list__pager')
            if not page_soup:
                return True, 0
            elif page_list := page_soup.find_all('div', class_='hidden'):
                return False, len(page_list) + 8
            else:
                return False, len(page_soup.find_all('ul', class_='full')) - 2
    except AttributeError:
        return


def to_xlsx():
    if DATA:
        df = pd.DataFrame(DATA)
        print(df)
        df.to_excel('ozon_parse.xlsx')


def to_json(data: dict) -> None:
    """Save database.

    The function take dict and save into JSON file.
    """
    try:
        if data:
            with open('json_parse.json', 'a') as file:
                json.dump(data, file, indent=4)
    except AttributeError as error:
        print(f'старница пуста - {error}')


def main():
    try:
        get_source_html(url=targetURL, pages=int(input('Кол-во страниц:')))
        to_xlsx()
        to_json(DATA)
        if DATA:
            print('\033[1;32;40m[INFO] Succese')
    except Exception as ex:
        print("\033[31m[ERROR]Ошибка, выполнение парсера было прервано")
        print(ex)


if __name__ == '__main__':
    main()
