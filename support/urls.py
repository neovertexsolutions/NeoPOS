from django.urls import path
from . import views

urlpatterns = [
    path('tickets/', views.support_ticket_list, name='support_ticket_list'),
    path('tickets/new/', views.support_ticket_create, name='support_ticket_create'),
    path('tickets/<uuid:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),
]
