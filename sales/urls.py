from django.urls import path
from . import views

urlpatterns = [
    path('pos/', views.pos_terminal, name='pos_terminal'),
    path('api/process-sale/', views.api_process_sale, name='api_process_sale'),
    path('', views.sales_list, name='sales_list'),
    path('<int:pk>/invoice/', views.invoice_detail, name='invoice_detail'),
]
