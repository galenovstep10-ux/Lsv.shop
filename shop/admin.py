from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import *


class OrderItemInline(admin.TabularInline):
    """Встраиваемые товары заказа"""
    model = OrderItem
    extra = 0
    fields = ['product', 'size', 'quantity', 'price', 'get_total']
    readonly_fields = ['product', 'size', 'quantity', 'price', 'get_total']
    can_delete = False
    verbose_name = "Товар"
    verbose_name_plural = "Товары в заказе"
    
    def get_total(self, obj):
        return f"{obj.price * obj.quantity} BYN"
    get_total.short_description = 'Сумма'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "price", "get_sizes_display")
    list_display_links = ("id", "title")
    search_fields = ("id", "title")
    list_filter = ("price",)
    
    def get_sizes_display(self, obj):
        if obj.sizes:
            return ", ".join(str(size) for size in obj.sizes)
        return "Не указаны"
    get_sizes_display.short_description = "Доступные размеры"
    
    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление всегда, независимо от связанных объектов"""
        return True
    
    def delete_queryset(self, request, queryset):
        """Переопределяем метод массового удаления"""
        for product in queryset:
            # Удаляем все связанные объекты вручную
            Photo.objects.filter(product=product).delete()
            OrderItem.objects.filter(product=product).delete()
            CartItem.objects.filter(product=product).delete()
        # После удаления всех связанных объектов, удаляем сами товары
        super().delete_queryset(request, queryset)
    
    def delete_model(self, request, obj):
        """Переопределяем метод удаления одного объекта"""
        # Удаляем все связанные объекты вручную
        Photo.objects.filter(product=obj).delete()
        OrderItem.objects.filter(product=obj).delete()
        CartItem.objects.filter(product=obj).delete()
        # Удаляем сам товар
        obj.delete()


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "product")
    list_display_links = ("id", "title")
    search_fields = ("id", "title")
    list_filter = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "city", "contact_info", "created_at", "status", "get_total_price")
    list_display_links = ("id", "full_name")
    search_fields = ("id", "full_name", "city", "contact_info", "user__username")
    list_filter = ("status", "created_at", "city")
    list_editable = ("status",)
    readonly_fields = ("created_at", "user", "display_order_items", "display_total")
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('status', 'created_at')
        }),
        ('Данные покупателя', {
            'fields': ('full_name', 'city', 'contact_info')
        }),
        ('Информация о пользователе', {
            'fields': ('user',),
            'classes': ('wide',)
        }),
        ('Состав заказа', {
            'fields': ('display_order_items', 'display_total'),
            'classes': ('wide',)
        }),
    )
    
    inlines = [OrderItemInline]
    
    def get_total_price(self, obj):
        """Общая сумма заказа для списка"""
        total = sum(item.price * item.quantity for item in obj.items.all())
        return format_html('<strong style="color: #2c6e2c;">{} BYN</strong>', total)
    get_total_price.short_description = 'Сумма'
    
    def display_order_items(self, obj):
        """Упрощенное отображение товаров в заказе"""
        items = obj.items.all()
        if not items:
            return "Нет товаров"
        
        items_list = []
        for item in items:
            size_info = f" (размер {item.size})" if item.size else ""
            items_list.append(
                f"• {item.product.title}{size_info} - {item.quantity} шт. x {item.price} BYN = {item.price * item.quantity} BYN"
            )
        
        return "<br>".join(items_list)
    display_order_items.short_description = 'Заказанные товары'
    
    def display_total(self, obj):
        """Отображение общей суммы"""
        total = sum(item.price * item.quantity for item in obj.items.all())
        return format_html(
            '<div style="background: #f0f9f0; padding: 15px; border-radius: 8px; margin-top: 10px;">'
            '<h3 style="margin: 0; color: #2c6e2c;">Итого: {} BYN</h3>'
            '</div>',
            total
        )
    display_total.short_description = 'Общая сумма'
    
    def get_queryset(self, request):
        """Оптимизация запросов для избежания N+1"""
        return super().get_queryset(request).prefetch_related('items__product')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "size", "quantity", "price", "get_total")
    list_display_links = ("id",)
    search_fields = ("order__id", "product__title", "size")
    list_filter = ("product", "size")
    readonly_fields = ("order", "product", "size", "quantity", "price")
    
    def get_total(self, obj):
        return f"{obj.price * obj.quantity} BYN"
    get_total.short_description = 'Сумма'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class CartItemInline(admin.TabularInline):
    """Встраиваемые товары корзины для просмотра в админке"""
    model = CartItem
    extra = 0
    fields = ['product', 'size', 'quantity', 'get_total']
    readonly_fields = ['product', 'size', 'quantity', 'get_total']
    can_delete = False
    
    def get_total(self, obj):
        return f"{obj.product.price * obj.quantity} BYN"
    get_total.short_description = 'Сумма'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at", "get_items_count", "get_total_price")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "created_at", "updated_at", "display_items", "get_total_price")
    inlines = [CartItemInline]
    
    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Кол-во товаров'
    
    def get_total_price(self, obj):
        total = sum(item.product.price * item.quantity for item in obj.items.all())
        return f"{total} BYN"
    get_total_price.short_description = 'Общая сумма'
    
    def display_items(self, obj):
        items = obj.items.all()
        if not items:
            return "Корзина пуста"
        
        items_list = []
        for item in items:
            size_info = f" (Размер: {item.size})" if item.size else ""
            items_list.append(
                f"• {item.product.title}{size_info} - {item.quantity} шт. x {item.product.price} BYN = {item.product.price * item.quantity} BYN"
            )
        
        return "<br>".join(items_list)
    display_items.short_description = 'Товары в корзине'