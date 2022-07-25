import sys
import requests
import json
import logging
from tqdm.auto import tqdm


def token_filter(log: logging.LogRecord) -> int:
    # фильтр логгера, чтобы он е выводил значения с token
    if 'token' in str(log.msg):
        return 0
    else:
        return 1


def new_logger(name):
    # создание логгера, который выводит логи в консоль и пишет в файл
    logger = logging.getLogger(name)
    FORMAT = "%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(FORMAT))
    sh.setLevel(logging.DEBUG)
    fh = logging.FileHandler(filename='Kursolog.log')
    fh.setFormatter(logging.Formatter(FORMAT, datefmt='%H:%M:%S'))
    fh.setLevel(logging.DEBUG)
    fh.addFilter(token_filter)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.debug('Logger initiated')


def find_error(some_dict):
    # Логирование ошибок и исключений в request-запросах
    try:
        if 'error' in some_dict:
           logger.error(f'Error code - {some_dict["error"]["error_code"]}, error message - {some_dict["error"]["error_msg"]}')
           logger.info('Closing program')
           sys.exit()
    except Exception as ex:
        logger.exception(f'Error code - {some_dict["error"]}, error message - {some_dict["message"]}')
        logger.info('Closing program')
        sys.exit()

new_logger('Kurs')
logger = logging.getLogger('Kurs.main')

with open('yatoken.txt', 'r') as file_object:
    yatoken = file_object.read().strip()
with open('vktoken.txt', 'r') as file_object:
    vktoken = file_object.read().strip()


class YAdisk:
    def __init__(self, token):
        self.token = token

    def headers_list(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def create_folder(self):
        #Создание папки на Яндекс диске, ввод названия, проверка на существующие, возвращает название папки
        logger.debug(f'Creating folder at YaDisk')
        folder_name = input('Задайте название папки на YaDisk:')
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.headers_list()
        params = {"path": folder_name}
        res = requests.put(url, headers=headers, params=params, stream=True).json()
        if 'error' in res:
            x = input(f" {res['message']} Нажмите '1' для записи в данную папку, или '2' для создания новой папки:")
            if x == '2':
                return self.create_folder()
            elif x == '1':
                return folder_name
        else:
            return folder_name


# get_upload_yalink(self, file_path):
        #logger.debug('Getting uploader link at YaDisk')
        #upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload/"
        #headers = self.headers_list()
        #params = {"path": f'/{file_path}', "overwrite": "true"}
        #response = requests.get(upload_url, headers=headers, params=params)
        #return response.json()


    def upload_file(self, file_path, filename):
        #загрузка фото на Яндекс диск
        logger.debug(f'Uploading file {file_path.split("/")[1]} to YaDisk')
        #response_href = self.get_upload_yalink(file_path=file_path).get('href', '')
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.headers_list()
        params = {"path": file_path, "url": filename}
        response = requests.post(url, headers=headers, params=params, stream=False)
        find_error(response.json())


class VKAcc:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

    def get_albums(self, vk_id):
        #извлекает список альбомов пользователя и возвращает ID выбранных для копирования альбомов
        logger.debug(f'Downloading list of albums from user_id {vk_id}')
        albums_url = self.url + 'photos.getAlbums'
        album_params = {
            'owner_id': vk_id,
            'photo_sizes': 1,
            }
        res = requests.get(albums_url, params={**self.params, **album_params}, stream=True).json()
        find_error(res)
        print('Список альбомов пользователя:')
        for i in res['response']['items']:
            print(f" ID альбома: {i['id']}, название альбома: {i['title']}")
        album_id = input('Введите ID альбомов через запятую:')
        return album_id

    def get_photo_q(self, vk_id, album_id):
        #извлекает кол-во фото в заданном альбоме и записывает в переменную кол-во для копирования
        photos_url = self.url + 'photos.get'
        photos_params = {
            'owner_id': vk_id,
            'album_id': album_id,
            }
        res = requests.get(photos_url, params={**self.params, **photos_params}, stream=True).json()
        find_error(res)
        print(f"Количество фотографий в альбоме:{res['response']['count']}")
        x = input('Введите количество фотографий для скачивания:')
        return x

    def get_photos(self, vk_id, photo_count, album_id):
        #Возвращает словарь с URL фотографий и записывает данные фото по заданию в json файл на компьютере
        logger.debug(f'Downloading {photo_count} photos from user_id {vk_id}')
        photos_url = self.url + 'photos.get'
        photos_params = {
            'owner_id': vk_id,
            'album_id': album_id,
            'extended': 1,
            'photo_sizes': 1,
            'count': photo_count,
            }
        res = requests.get(photos_url, params={**self.params, **photos_params}, stream=True).json()
        find_error(res)
        results_list = []
        count_list = []
        count = 0
        for i in res['response']['items']:
            count += 1
            if i['likes']['count'] in count_list:
                results_list.append(dict(filename=f"{i['likes']['count']}_{(i['date'])}_{count}.jpg",
                                         size=i['sizes'][-1]['type'],
                                         url=i['sizes'][-1]['url']))
            else:
                count_list.append(i['likes']['count'])
                results_list.append(dict(filename=f"{i['likes']['count']}.jpg",
                                         size=i['sizes'][-1]['type'],
                                         url=i['sizes'][-1]['url']))

        with open('Resultsfile.json', "w", encoding='UTF-8') as file:
            logger.debug(f'writing list of photos in the file {file}')
            some_temp = []
            for i in results_list:
                some_temp.append({'filename': i['filename'], 'size': i['size']})
            json.dump(some_temp, file, ensure_ascii=False, indent=2)

        return results_list


def command_control():
    #Вызывает пользовательское меню и загружает выбранные фото на яндекс диск
    x = input("Загрузить фото профиля - '1' , фото со стены - '2', сохраненные фото - '3', для загрузки альбомов '4':")
    no_id = input("Введите ID профиля:")
    #yatoken = input("Введите token YaDisk:") #по ТЗ нужно вводить токен вручную
    vk_client = VKAcc(vktoken, '5.131')

    if x == '1':
        choose_album_id = 'profile'

    elif x == '2':
        choose_album_id = 'wall'

    elif x == '3':
        choose_album_id = 'saved'

    elif x == '4':
        choose_album_id = vk_client.get_albums(no_id)

    else:
        print("Команда введена неверно, повторите ввод.")
        return command_control()


    for i in list(choose_album_id.split(',')):
        no_of_phot = vk_client.get_photo_q(no_id, i)
        result = vk_client.get_photos(no_id, no_of_phot, i)
        yadisk = YAdisk(yatoken)
        folder_name1 = yadisk.create_folder()
        with tqdm(total=len(result), unit_scale=True, initial=1, colour="GREEN") as pbar:
            for b in result:
                name = f"{folder_name1}/"+f"{b['filename']}"
                yadisk.upload_file(file_path=name, filename=b['url'])
                pbar.update(1)


if __name__ == '__main__':
    logger.info('Starting program')
    command_control()
    logger.info('Closing program')

