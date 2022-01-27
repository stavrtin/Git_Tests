import time
import requests
import pymysql
import datetime
from getpass import getpass


def connect_to_db(connection_data):
    return pymysql.connect(
                host=connection_data[0],
                user=connection_data[1],
                password=connection_data[2],
                database='reputation')


def get_reviews(url, fk_pars_links):
    while True:
        r = requests.get(url).json()
        reviews = r['reviews']
        for review in reviews:
            user_data = review['user']
            idres = review['id']
            user_id = user_data['id']
            title = user_data['name']
            comments = user_data['reviews_count']
            date_reviews = review['date_created'].split('T')[0]
            stars = review['rating']
            comment = review['text']
            link = review['url']
            with connect_to_db(con) as connect:
                with connect.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM `reviews` WHERE `idres`={idres}")
                    if cursor.fetchone() is None:
                        cursor.execute(f"INSERT INTO `reviews`(`idres`, `title`, `date_reviews`, `comment`, `stars`, `comments`, `fk_pars_links`,`link`) VALUES ({idres},'{title}','{date_reviews}','{comment}',{stars},{comments},{fk_pars_links},'{link}')")
                        connect.commit()
                        print(title)
                        print(f'Кол-во звёзд: {stars}')
                        print(comment)
                        print('\n')
        try:
            url = r['meta']['next_link']
        except KeyError:
            break


def main():
    with connect_to_db(con) as connect:
        with connect.cursor() as cursor:
            cursor.execute("SELECT `pars_link`, `fk_city_adress` FROM `pars_links` WHERE `fk_source` = 1")
            branches = cursor.fetchall()
            for i in branches:
                j = i[0].split('/')
                firm_id = j[j.index('firm') + 1]
                get_reviews(
                    f'https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews?limit=50&is_advertiser=false&fields=meta.providers,meta.branch_rating,meta.branch_reviews_count,meta.total_count,reviews.hiding_reason,reviews.is_verified&without_my_first_review=false&rated=true&sort_by=date_edited&key=37c04fe6-a560-4549-b459-02309cf643ad&locale=ru_RU',
                    i[1])


if __name__ == '__main__':
    host = input('Хост: ')
    user = input('Пользователь: ')
    password = getpass(prompt='Пароль: ')
    con = [host, user, password]
    while True:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '[INFO] Сбор данных')
        main()
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '[INFO] Следующий сбор через 12 часов')
        time.sleep(43200)
