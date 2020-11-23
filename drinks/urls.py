from django.urls import path

from drinks import views


app_name = 'drinks'
urlpatterns = [
    path('', views.drink_list, name='list'),
    path('download/', views.drink_download, name='download'),
]
