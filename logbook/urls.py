from django.urls import path
from . import views

urlpatterns = [
    path('', views.batch_list, name='batch_list'),
    path('register/', views.register, name='register'),
    path('add/', views.add_batch, name='add_batch'),
    path('batch/<int:batch_id>/', views.view_batch, name='view_batch'),
    path('search/', views.search_batches, name='search_batches'),
]