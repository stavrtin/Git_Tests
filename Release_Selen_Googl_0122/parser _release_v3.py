import time
import requests
import pymysql
import datetime
from getpass import getpass

from datetime import time, date, datetime, timedelta
import time, datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as se
import mysql.connector
from mysql.connector import Error
from selenium.webdriver.common.action_chains import ActionChains

import hashlib
import re

def get_hash(str_text):
    ''' для проверки уникальности записи не придумал ничего лучше, как создать хэш
    от состоит из имени пользователя и количества постов (на данный момент) '''
    hash_object = hashlib.md5(str_text.encode()) # получаю тект (имя+кол.постов) хэштрую
    reg = re.compile('[^0-9]')                # чищу от символов кроме цифр (в БД поле в которое только int записывается)
    hex_hash = reg.sub('', hash_object.hexdigest())[:5] # обрезаю хэш до 5 знаков - ну достаточно думаю.
    return hex_hash



def get_date_of_post(data_str):
    '''функция переводит дату отзыва в фотрмат даты'''
    t_now = ['что']
    yesterday = ['вчера']
    one_week = ['неделя', 'неделю']
    one_mounth = ['месяц']
    one_year = ['год']
    t_today = ['день', 'час', 'минуту']
    minute = ['минут', 'минуты', 'минуту']
    hour = ['час', 'часа', 'часов']
    day = ['день', 'дня', 'дней']
    week = ['недели', 'неделю', 'недель']
    mounth = ['месяца', 'месяц', 'месяцев']
    year = ['год', 'года', 'лет']

    # for item in text:
    if data_str.split(' ')[0] in t_today: data_time = date.today()
    if data_str.split(' ')[0] in one_week: data_time = date.today() - timedelta(7)
    if data_str.split(' ')[0] in one_mounth: data_time = date.today() - timedelta(30)
    if data_str.split(' ')[0] in one_year: data_time = date.today() - timedelta(365)
    if data_str.split(' ')[0] in yesterday: data_time = date.today() - timedelta(1)

    if data_str.split(' ')[1] in t_now: data_time = date.today()
    if data_str.split(' ')[1] in minute: data_time = date.today()
    if data_str.split(' ')[1] in hour: data_time = date.today()
    if data_str.split(' ')[1] in day: data_time = date.today() - timedelta((int(data_str.split(' ')[0])*1))
    if data_str.split(' ')[1] in week: data_time = date.today() - timedelta((int(data_str.split(' ')[0])*7))
    if data_str.split(' ')[1] in mounth: data_time = date.today() - timedelta((int(data_str.split(' ')[0])*30))
    if data_str.split(' ')[1] in year: data_time = date.today() - timedelta((int(data_str.split(' ')[0])*365))

    return data_time

def connect_to_db(connection_data):
    '''соединение с базой данных'''
    return pymysql.connect(
                host=connection_data[0],
                user=connection_data[1],
                password=connection_data[2],
                # database='reputation'
                database='parser_object'
                )


# def get_reviews(url, fk_pars_links):
def get_reviews(url):
    '''получение собственно отзыва'''
    # подключаю селениум - драйвер для хрома
    options = webdriver.ChromeOptions()
    binary_chrome_driver_file = "C:\chromedriver.exe"   # драйвер установил прямо в корень
    driver = webdriver.Chrome(binary_chrome_driver_file, options=options)
    # #

    driver.get(url)
    time.sleep(5)
    # начинаю процесс сбора данных - поиск тэгов
    # нашел кнопку 'svg' (не последнюю [-2]), которую нажимаю для получения возможности
    # "проскроливать" экран кнопкой END
    post = driver.find_elements(By.TAG_NAME, 'svg')[-2]
    actions = ActionChains(driver)
    actions.move_to_element(post)
    actions.click()
    actions.perform()

    # получаю количество откликов, записываю в count_posts
    try:
        count_posts = int(driver.find_element(By.CLASS_NAME, 'z5jxId').text.replace('отзывов', '').replace(' ', ''))
    except:
        count_posts = 1

    # по количеству откликов определяю - сколько раз нам надо нажать END, что бы перейти к
    # низу страницы (после этого страница автоматически обновляется - можно листать дальше)
    # количество откликов делю на кол-во откликов на странице (их 10) получаю,
    # организовываю цикл

    for j in range(1 + count_posts//10): # для полного сбора
    # for j in range(1):  # для тестовой отладки
        '''листает по 10 постов'''
        actions.key_down(Keys.CONTROL).key_down(Keys.END)    # нажатие кнопки CONTROL+END
        time.sleep(1)
        # организация задержки до момента полной прогрузки страницы
        element = WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'jxjCjc')))
        actions.perform() # спусковой крючек - собственно нажание кнопок
        print(f'Считывается {j * 10} из {count_posts} отзывов')

    # по тегу CLASS_NAME, 'jxjCjc', в которые записаны отзывы - считаю их количество
    posts = driver.find_elements(By.CLASS_NAME, 'jxjCjc')
    print(f'Собрано {len(posts)} записей')

    count_date = 0  # не получалось найти каким тегом собрать даты публикаций - пришлось подбирать переменную
                    # пускать ее внутри цикла и к ней привязывать тег с текстом по дате поста
    for item in posts:
        post_dict = {}

        try:     name = item.find_element(By.CLASS_NAME, 'TSUbDb').text.replace("'",'')
        except:  name = 'None'

        try:     text = item.find_element(By.CLASS_NAME, 'Jtu6Td').text
        except:  text = 'None'

        try:     mark = int(item.find_element(By.TAG_NAME, 'g-review-stars').find_element(By.TAG_NAME, 'span').get_attribute(
                'aria-label').replace(',0 из 5,', '').replace('Оценка: ', '').replace(',', '.'))
        except:  mark = 0

        try:     date_post = get_date_of_post(item.find_elements(By.XPATH, '//span[contains(@class,"dehysf lTi8oc")]')[count_date].text)
        except:  date_post = date.today() - timedelta(1)
        count_date += 1

        try:
            comments = item.find_element(By.CLASS_NAME, 'A503be').text.replace('Местный эксперт', '')
            comments = [i for i in comments.split('·') if i.find('отзыв') > 0]
            comments = int(comments[0].split(' ')[0])
        except:
            comments = 1

        now = datetime.datetime.today().replace(microsecond=0)
        user_data = now

        # собрал данные для передачи в базу
        title = name
        comments = comments
        date_reviews = date_post
        stars = mark
        comment = text
        link = ''
        # для проверки уникальности записи не придумал ничего лучше, как создать хэш
        # от состоит из имени пользователя и количества постов (на данный момент)

        idres = get_hash(name + str(comments))

        with connect_to_db(con) as connect:  # подключаю БД
            with connect.cursor() as cursor:
                cursor.execute(f'SELECT * FROM `reviews` WHERE `idres`={idres}') # запрос на проверку уникальности записи по хэш
                if cursor.fetchone() is None:    # если записи еще не было делаем INSERT по нужным нам полям
                    cursor.execute(f"INSERT INTO `reviews`(`idres`, `title`, `date_reviews`, `comment`, `stars`, `comments`, `fk_pars_links`,`link`, `date_creat`) VALUES ({idres},'{title}','{date_reviews}','{comment}',{stars},{comments},{11},'{link}','{user_data}')")
                    connect.commit()
                    # print(title)     # можно включить принтыю При записи в консоле LINUX будет отражаться, что идет код
                    # print(f'Кол-во звёзд: {stars}')
                    # print(comment)
                    # print('\n')
        # для  перебора ссылок из внешней таблицы по url объектов, которые будем парсить
        # try:
        #     url = r['meta']['next_link']
        # except KeyError:
        #     break


def main():
    url = 'https://inlnk.ru/84PyVk'
    get_reviews(url)


if __name__ == '__main__':
    # host = input('Хост: ')  можно вводить ручками параметры - куда на какой сервер скидывать
    # user = input('Пользователь: ')
    # password = getpass(prompt='Пароль: ')

    # параметры - куда на какой сервер скидывать для ЗАКАЗЧИКА
    # host='95.142.47.29'
    # user = 'admin'
    # password = '0fuA~q'

    con = [host, user, password]
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '[INFO] Сбор данных')
    start_time = time.time()
    main()
    print(f"--- Общее время работы парсера \t{round((time.time() - start_time), 2)} seconds ---")

    # while True:
    #     '''Организация бесконечного цикла работы (периодичность нижним таймером)'''
    #     print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '[INFO] Сбор данных')
    #     start_time = time.time()
    #     main()
    #
    #     print(f"--- Общее время работы парсера \t{round((time.time() - start_time), 2)} seconds ---")
    #     print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '[INFO] Следующий сбор через 12 часов')
    #     time.sleep(43200)
