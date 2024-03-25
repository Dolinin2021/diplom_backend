"""
URL configuration for cloud project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from app.views import FileAPIListAdmin, FileAPIListUser, FileDetailAPIView, UserList, UpdateUserParams, UserAdd, UserInfo, download_share

urlpatterns = [
    path('admin/', admin.site.urls),
    path('back/useradd/', UserAdd.as_view()),
    path('back/userlist/', UserList.as_view()),
    path('back/userlist/<int:pk>/', UserInfo.as_view()),
    path('back/user/change/<int:pk>/', UpdateUserParams.as_view()),
    path('back/api/v1/filelist/', FileAPIListUser.as_view()),
    path('back/api/v1/filelist/<int:pk>/', FileAPIListAdmin.as_view()),
    path('back/api/v1/filelist/detail/<int:pk>/', FileDetailAPIView.as_view()),
    path('back/api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('back/api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('back/api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('file/download/', download_share)
]

urlpatterns += static('files/', document_root=os.path.join(settings.MEDIA_ROOT, 'files'))
