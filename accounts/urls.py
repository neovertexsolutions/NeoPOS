from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.users_list, name='users_list'),
    path('manage-action/', views.manage_user_action, name='manage_user_action'),
    path('generate-license/', views.generate_license_action, name='generate_license_action'),
    path('manage-license-key-option/<int:option_id>/', views.manage_license_key_option_action, name='manage_license_key_option_action'),
    path('manage-license/<int:license_id>/', views.manage_license_action, name='manage_license_action'),
    path('activate-license/', views.activate_license_view, name='activate_license'),
    path('upgrade/', views.upgrade_request_view, name='upgrade_request'),
    path('profile/', views.profile_view, name='profile'),
]
