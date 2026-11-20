from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('history/', views.movement_history, name='movement_history'),
]
