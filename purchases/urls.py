from django.urls import path
from . import views

urlpatterns = [
    path('', views.purchases_list, name='purchases_list'),
    path('add/', views.purchase_add, name='purchase_add'),
    path('<int:pk>/', views.purchase_detail, name='purchase_detail'),
]
