import logging
import os
import uuid
import shutil

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import FileResponse
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import File, file_path
from .serializers import FileListSerializer, FileDetailSerializer, UserSerializer, UserChanger

logging.basicConfig(level=logging.INFO, filename="my_cloud.log", filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")

user = get_user_model()


def download_share(request):
    file_uuid = request.GET.get('share')
    obj = File.objects.get(share=file_uuid)
    filename = obj.file.path
    response = FileResponse(open(filename, 'rb'))
    return response


# Информация о конкретном пользователе

class UserInfo(generics.ListAPIView):
    queryset = user.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        try:
            user_obj = user.objects.get(id=self.kwargs['pk'])
            quantity_files = File.objects.filter(user=user_obj.id).count()
            user_info = {"userInfo": {"admin": user_obj.is_superuser,
                                      "name": user_obj.username,
                                      "firstName": user_obj.first_name,
                                      "lastName": user_obj.last_name,
                                      "email": user_obj.email,
                                      "lastLogin": user_obj.last_login,
                                      "userId": user_obj.id,
                                      "quantityFiles": quantity_files}}
            return Response(user_info)
        except ObjectDoesNotExist:
            return Response(
                data={'error': {'code': 404, 'msg': 'Нет данных'}}, content_type='application/json',
                status=status.HTTP_404_NOT_FOUND)


# Добавление нового пользователя

class UserAdd(generics.ListCreateAPIView):
    queryset = user.objects.all().order_by('date_joined')
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        if 'password' in self.request.data:
            password = make_password(self.request.data['password'])
            serializer.save(password=password)
        else:
            serializer.save()


# Список пользователей

class UserList(generics.ListAPIView):
    queryset = user.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        all_users = [users for users in user.objects.values("id",
                                                            "username",
                                                            "last_login",
                                                            "email",
                                                            "is_superuser",
                                                            "is_active",
                                                            "first_name",
                                                            "last_name", ) if request.user.id != users['id']]
        return Response({"allUsers": sorted(all_users, key=lambda d: d['id'])})


# Изменение параметров пользователя, а также удаление пользователя

class UpdateUserParams(generics.RetrieveUpdateDestroyAPIView):
    queryset = user.objects.all()
    serializer_class = UserChanger
    authentication_classes = (JWTAuthentication,)
    permission_classes = [permissions.IsAuthenticated, ]

    def delete(self, request, *args, **kwargs):
        req_user_name = user.objects.get(username=self.request.user)
        try:
            user_obj = user.objects.get(id=self.kwargs['pk'])
            if req_user_name.is_superuser:
                try:
                    shutil.rmtree(f'{settings.MEDIA_ROOT}/files/storages/{user_obj.id}/')
                except FileNotFoundError:
                    ...
                finally:
                    return self.destroy(request, *args, **kwargs)
            else:
                return Response(
                    data={'error': {'code': 403, 'msg': 'Нет необходимых разрешений для использования метода '
                                                        'DELETE'}}, content_type='application/json',
                    status=status.HTTP_403_FORBIDDEN)
        except ObjectDoesNotExist:
            return Response(
                data={'error': {'code': 404, 'msg': 'Нет данных'}}, content_type='application/json',
                status=status.HTTP_404_NOT_FOUND)


# Список файлов конкретного пользователя,
# а также добавление нового файла в файловое хранилище конкретного пользователя

class FileAPIListAdmin(generics.ListCreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileListSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        req_user_name = user.objects.get(username=self.request.user)
        if req_user_name.is_superuser:
            try:
                user_obj = user.objects.get(id=self.kwargs['pk'])
                file = File.objects.filter(user=user_obj.id)
                logging.info(f'Обзор списка файлов администратором: {req_user_name}')
                print(f'Обзор списка файлов администратором: "{req_user_name}"')
                return self.queryset.filter(user=user_obj).order_by('id')
            except ObjectDoesNotExist:
                return Response(
                    data={'error': {'code': 404, 'msg': 'Нет данных'}}, content_type='application/json',
                    status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(
                data={'error': {'code': 403, 'msg': 'Нет необходимых разрешений для просмотра файлового хранилища '
                                                    'заданного пользователя'}},
                content_type='application/json',
                status=status.HTTP_403_FORBIDDEN)


# Список файлов текущего пользователя,
# а также добавление нового файла в файловое хранилище текущего пользователя

class FileAPIListUser(generics.ListCreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileListSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        try:
            req_user_name = user.objects.get(username=self.request.user)
            logging.info(f'Обзор списка файлов пользователем: {req_user_name}')
            print(f'Обзор списка файлов пользователем: "{req_user_name}"')
            return self.queryset.filter(user=req_user_name).order_by('id')
        except ObjectDoesNotExist:
            return Response(
                data={'error': {'code': 404, 'msg': 'Нет данных'}}, content_type='application/json',
                status=status.HTTP_404_NOT_FOUND)


# Работа с текущим файлом (получение данных, генерация ссылки, обновление,  удаление)

class FileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = File.objects.all()
    serializer_class = FileDetailSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        try:
            logging.info(f"Обзор файла: {File.objects.get(id=self.kwargs['pk'])}")
            print(f"Обзор файла: {File.objects.get(id=self.kwargs['pk'])}")
            return self.retrieve(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return Response(
                data={'error': {'code': 404, 'msg': 'Нет данных'}}, content_type='application/json',
                status=status.HTTP_404_NOT_FOUND)

    def put(self, request, *args, **kwargs):
        instance = File.objects.get(id=self.kwargs['pk'])
        instance.share = uuid.uuid4()
        logging.info(f"Ссылка создана: {request.build_absolute_uri('/')}file/download/?share={instance.share}")
        print(f"Ссылка создана: {request.build_absolute_uri('/')}file/download/?share={instance.share}")
        instance.url = f"{request.build_absolute_uri('/')}file/download/?share={instance.share}"
        instance.save()
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        try:
            instance = File.objects.get(id=self.kwargs['pk'])
            for item in request.data:
                if item == 'title':
                    new_path_file = file_path(instance, request.data[item])
                    self.update(request, *args, **kwargs)
                    try:
                        full_old_path_file = os.path.join(settings.MEDIA_ROOT, str(instance.file))
                        full_new_path_file = os.path.join(settings.MEDIA_ROOT, new_path_file)
                        os.rename(full_old_path_file, full_new_path_file)
                        instance.title = request.data[item]
                        instance.file = new_path_file
                        instance.save()
                    except FileNotFoundError:
                        return Response(
                            data={'error': {'code': 500, 'msg': 'Не удаётся найти указанный файл.'}},
                            content_type='application/json',
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    except FileExistsError:
                        return Response(
                            data={'error': {'code': 500, 'msg': 'Невозможно создать файл, так как он уже существует.'}},
                            content_type='application/json',
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            req_user_name = user.objects.get(username=self.request.user)
            logging.info(f'Обновление файла {instance} пользователем: {req_user_name}')
            print(f'Обновление файла {instance} пользователем: "{req_user_name}"')
            return self.partial_update(request, *args, **kwargs)

        except ObjectDoesNotExist:
            return Response(
                data={'error': {'code': 404, 'msg': 'Нет данных'}},
                content_type='application/json',
                status=status.HTTP_404_NOT_FOUND)
        except FileNotFoundError:
            return Response(
                data={'error': {'code': 500, 'msg': 'Не удаётся найти указанный файл.'}},
                content_type='application/json',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        try:
            instance = File.objects.get(id=self.kwargs['pk'])
            req_user_name = user.objects.get(username=self.request.user)
            logging.info(f'Удаление файла {instance} пользователем: {req_user_name}')
            print(f'Удаление файла {instance} пользователем: "{req_user_name}"')
            return self.destroy(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return Response(
                data={'error': {'code': 404, 'msg': 'Нет данных'}}, content_type='application/json',
                status=status.HTTP_404_NOT_FOUND)
