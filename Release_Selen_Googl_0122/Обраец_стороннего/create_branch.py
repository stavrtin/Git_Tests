import pymysql
from getpass import getpass


def connect_to_db(db):
    return pymysql.connect(
                host=db[0],
                user=db[1],
                password=db[2],
                database='reputation')


def main():
    host = input('Хост: ')
    user = input('Пользователь: ')
    password = getpass(prompt='Пароль: ')
    db = [host, user, password]
    with connect_to_db(db) as connect:
        with connect.cursor() as cursor:
            cursor.execute("SELECT `id`, `name` FROM `city` ORDER BY `id`")
            for i in cursor.fetchall():
                print(f'{i[0]}) {i[1]}')
            city_id = int(input('Введите номер города(0 - если создать новый): '))
            if city_id == 0:
                city = input('Введите название города который хотите добавить: ').title()
                cursor.execute(f"INSERT INTO `city`(`name`) VALUES ('{city}');")
                connect.commit()
                cursor.execute(f"SELECT `id` FROM `city` WHERE `name` = '{city}'")
                city_id = cursor.fetchone()[0]
            cursor.execute("SELECT `id`, `name` FROM `adress` ORDER BY `id`")
            for i in cursor.fetchall():
                print(f'{i[0]}) {i[1]}')
            adress_id = int(input('Введите номер улицы(0 - если создать новый): '))
            if adress_id == 0:
                adress = input('Введите название улицы который хотите добавить: ')
                cursor.execute(f"INSERT INTO `adress`(`name`) VALUES ('{adress}')")
                connect.commit()
                cursor.execute(f"SELECT `id` FROM `adress` WHERE `name` = '{adress}'")
                adress_id = cursor.fetchone()[0]
            pars_link = input('Вставьте ссылку на филиал(обязательно 2gis): ')
            cursor.execute(f"SELECT `id` FROM `city_adress` WHERE `fk_city` = {city_id} AND `fk_adress` = {adress_id}")
            try:
                fk_city_adress = cursor.fetchone()[0]
            except TypeError:
                fk_city_adress = None
            if fk_city_adress is None:
                cursor.execute(f"INSERT INTO `city_adress`(`fk_city`, `fk_adress`) VALUES ({city_id}, {adress_id})")
                connect.commit()
                cursor.execute(
                    f"SELECT `id` FROM `city_adress` WHERE `fk_city` = {city_id} AND `fk_adress` = {adress_id}")
                fk_city_adress = cursor.fetchone()[0]
            cursor.execute(f"SELECT * FROM `pars_links` WHERE `fk_city_adress` = {fk_city_adress}")
            if cursor.fetchone() is None:
                cursor.execute(
                    f"INSERT INTO `pars_links`(`pars_link`, `fk_city_adress`, `fk_source`) VALUES ('{pars_link}', {fk_city_adress}, 1)")
                connect.commit()
                print('Филиал добавлен')
            else:
                print('Данный филиал уже в базе данных')


if __name__ == '__main__':
    main()
