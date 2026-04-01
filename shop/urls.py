from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views


urlpatterns=[
    path('', home_page, name='home'),
    path('product/<int:id>', product, name="product"),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart, name='update_cart'),
    path('cart/update-size/<int:item_id>/', update_cart_item_size, name='update_cart_item_size'),
    path('cart/checkout/', create_order, name='create_order'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),  # своя вьюха
    path('logout/', logout_view, name='logout'),
    path('order/<int:order_id>/success/', order_success, name='order_success'),

]