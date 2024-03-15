import datetime
import logging

logging.basicConfig(level=logging.INFO, filename="my_cloud.log", filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/files/storages/"):
            logging.info(f'Скачан файл: {str(request.path).rsplit("/", 1)[-1]}'
                         f'\nОтносительный путь: {str(request.path)}'
                         f'\nВремя и дата скачивания: {datetime.datetime.now()}')
            print(
                f'Скачан файл: {str(request.path).rsplit("/", 1)[-1]}'
                f'\nОтносительный путь: {str(request.path)}'
                f'\nВремя и дата скачивания: {datetime.datetime.now()}'
            )
        return self.get_response(request)
