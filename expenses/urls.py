from django.urls import path
from . import views

urlpatterns = [
    path('', views.expenses_list, name='expenses_list'),
    path('categories/', views.expense_categories, name='expense_categories'),
    path('<int:pk>/delete/', views.expense_delete, name='expense_delete'),
]
