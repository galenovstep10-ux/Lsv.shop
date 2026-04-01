from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, Http404
from .models import *
from .forms import OrderForm
from .forms import RegisterForm


def get_cart_count(user):
    """Вспомогательная функция для получения количества товаров в корзине"""
    if user.is_authenticated:
        cart = Cart.objects.filter(user=user).first()
        if cart:
            return cart.items.count()
    return 0


def home_page(request):
    """Главная страница с поиском"""
    products = Product.objects.all()
    
    # Получаем поисковый запрос
    search_query = request.GET.get('q', '').strip()
    
    if search_query:
        # Поиск по названию, описанию и другим полям
        products = products.filter(
            Q(title__icontains=search_query) |  # Поиск в названии
            Q(content__icontains=search_query)   # Поиск по бренду (если есть поле)
        )
    
    context = {
        "products": products,
        "search_query": search_query,
        "products_count": products.count(),
        "cart_items_count": get_cart_count(request.user)
    }
    return render(request, 'index.html', context)


def product(request, id):
    product = Product.objects.get(id=id)
    photos = Photo.objects.filter(product=id)
    available_sizes = product.sizes if product.sizes else [36, 37, 38, 39, 40, 41, 42, 43, 44]
    
    context = {
        "product": product,
        "title": product.title,
        "photos": photos,
        "description": product.content,
        "sizes": available_sizes,
        "cart_items_count": get_cart_count(request.user)
    }
    return render(request, 'product.html', context)


@login_required
def create_order(request):
    """Оформление заказа из корзины"""
    cart = Cart.objects.filter(user=request.user).first()
    
    if not cart or not cart.items.exists():
        messages.error(request, 'Корзина пуста')
        return redirect('home')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Создаём заказ
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            
            # Переносим товары из корзины в заказ
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    size=item.size,
                    quantity=item.quantity,
                    price=item.product.price
                )
            
            # Очищаем корзину
            cart.items.all().delete()
            
            messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            return redirect('order_success', order_id=order.id)
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'cart': cart,
        'total': cart.get_total_price(),
        'cart_items_count': cart.items.count()
    }
    return render(request, 'create_order.html', context)


@login_required
def cart_detail(request):
    """Страница корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Отладочная информация
    print(f"Cart for user {request.user.username}:")
    for item in cart.items.all():
        print(f"  Item ID: {item.id}, Product: {item.product.title}, Size: {item.size}")
    
    context = {
        'cart': cart,
        'cart_items_count': cart.items.count()
    }
    return render(request, 'cart.html', context)


@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину с размером"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Получаем размер и количество из POST запроса
    size = request.POST.get('size')
    quantity = int(request.POST.get('quantity', 1))
    
    # Проверяем, что размер выбран
    if not size:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Пожалуйста, выберите размер'})
        messages.error(request, 'Пожалуйста, выберите размер')
        return redirect('product', id=product_id)
    
    # Проверяем, что размер доступен
    available_sizes = product.sizes if product.sizes else [36, 37, 38, 39, 40, 41, 42, 43, 44]
    try:
        if int(size) not in available_sizes:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Выбранный размер недоступен'})
            messages.error(request, 'Выбранный размер недоступен')
            return redirect('product', id=product_id)
    except ValueError:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Некорректный размер'})
        messages.error(request, 'Некорректный размер')
        return redirect('product', id=product_id)
    
    # Ищем товар с таким же размером в корзине
    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product,
        size=str(size)  # Преобразуем в строку для сравнения
    ).first()
    
    if cart_item:
        # Если товар с таким размером уже есть, увеличиваем количество
        cart_item.quantity += quantity
        cart_item.save()
        message = f'Количество товара "{product.title}" (размер {size}) увеличено'
        success = True
    else:
        # Создаем новую запись с выбранным размером
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            size=str(size),
            quantity=quantity
        )
        message = f'Товар "{product.title}" (размер {size}) добавлен в корзину'
        success = True
    
    # Обработка AJAX запроса
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'message': message,
            'cart_total': cart.get_total_price(),
            'cart_count': cart.items.count(),
            'item_id': cart_item.id
        })
    
    messages.success(request, message)
    return redirect('cart_detail')


@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины с улучшенной обработкой ошибок"""
    try:
        # Пытаемся найти CartItem, принадлежащий текущему пользователю
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = cart_item.product.title
        size_info = f" (размер {cart_item.size})" if cart_item.size else ""
        cart_item.delete()
        messages.success(request, f'Товар "{product_name}"{size_info} удалён из корзины')
        
    except Http404:
        # Если элемент не найден, выводим сообщение об ошибке
        messages.error(request, f'Товар с ID {item_id} не найден в вашей корзине')
    
    return redirect('cart_detail')


@login_required
def update_cart(request, item_id):
    """Обновление количества товара"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if request.method == 'POST':
            quantity = int(request.POST.get('quantity', 1))
            size = request.POST.get('size')
            
            if quantity > 0:
                cart_item.quantity = quantity
                if size:  # Если передан новый размер
                    cart_item.size = str(size)
                cart_item.save()
                messages.success(request, 'Количество обновлено')
            else:
                cart_item.delete()
                messages.success(request, 'Товар удалён')
        
    except Http404:
        messages.error(request, f'Товар с ID {item_id} не найден в вашей корзине')
    
    return redirect('cart_detail')


@login_required
def update_cart_item_size(request, item_id):
    """Обновление размера товара в корзине"""
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            new_size = request.POST.get('size')
            
            if new_size:
                # Проверяем, есть ли уже товар с таким размером в корзине
                existing_item = CartItem.objects.filter(
                    cart=cart_item.cart,
                    product=cart_item.product,
                    size=str(new_size)
                ).exclude(id=cart_item.id).first()
                
                if existing_item:
                    # Если есть, объединяем количество
                    existing_item.quantity += cart_item.quantity
                    existing_item.save()
                    cart_item.delete()
                    message = f'Размер изменен на {new_size}, количество объединено'
                    success = True
                else:
                    # Просто обновляем размер
                    cart_item.size = str(new_size)
                    cart_item.save()
                    message = f'Размер изменен на {new_size}'
                    success = True
            else:
                message = 'Размер не указан'
                success = False
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': success, 'message': message})
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        except Http404:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Товар не найден в корзине'})
            messages.error(request, 'Товар не найден в корзине')
    
    return redirect('cart_detail')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('/')
    else:
        form = RegisterForm()
    
    context = {
        'form': form,
        'cart_items_count': get_cart_count(request.user)
    }
    return render(request, 'register.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('/')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    context = {
        'cart_items_count': get_cart_count(request.user)
    }
    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из аккаунта')
    return redirect('/')


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
        'cart_items_count': get_cart_count(request.user)
    }
    return render(request, 'order_success.html', context)