from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_landing, name='home'),
    path('about/', views.about_page, name='about_page'),
    path('pricing/', views.pricing_page, name='pricing_page'),
    path('contact/', views.contact_page, name='contact_page'),
    path('pos-showcase/', views.pos_showcase_page, name='pos_showcase_page'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('security/', views.security, name='security'),
    path('hardware-support/', views.hardware_support, name='hardware_support'),
]
