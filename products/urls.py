from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_add, name='product_add'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('barcodes/', views.barcode_list, name='barcode_list'),
    path('qrcodes/', views.qrcode_list, name='qrcode_list'),
    path('labels/', views.label_list, name='label_list'),
    path('<int:pk>/barcode/', views.print_barcode, name='print_barcode'),
    path('<int:pk>/qrcode/', views.print_qrcode, name='print_qrcode'),
    path('<int:pk>/qrcode.png', views.qrcode_image, name='qrcode_image'),
    path('<int:pk>/label/', views.print_label, name='print_label'),
    path('api/search/', views.api_product_search, name='api_product_search'),
]
