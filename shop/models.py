from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


class Product(models.Model):
    title = models.CharField(max_length=200, blank=False, verbose_name="Название товара")
    content = models.TextField(max_length=4000, blank=False, verbose_name="Описание товара")
    price = models.DecimalField(max_digits=12, decimal_places=2, blank=False, verbose_name="Цена товара")
    image = models.ImageField(upload_to='product_images/')
    
    sizes = models.JSONField(default=list, blank=True, verbose_name="Доступные размеры")
    
    def __str__(self):
        return f"{self.id}.{self.title}"
    
    def get_absolute_url(self):
        return reverse('product', kwargs={"id": self.id})
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["id",]


class Photo(models.Model):
    title = models.CharField(max_length=200, blank=False, verbose_name="Фотография")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # CASCADE - удалит фото при удалении товара
    photo = models.ImageField(upload_to='product_images')
    
    def __str__(self):
        return f"{self.id}{self.title}"
    
    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"
        ordering = ["id",]


User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name='Покупатель'
    )
    
    full_name = models.CharField('ФИО', max_length=255)
    city = models.CharField('Город', max_length=100)
    contact_info = models.CharField('Контактная информация', max_length=255, null=False)
    
    created_at = models.DateTimeField('Дата заказа', auto_now_add=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Заказ #{self.id} от {self.full_name}'


class OrderItem(models.Model):
    """Товары в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='Товар')  # CASCADE - удалит позиции заказа
    size = models.CharField('Размер', max_length=20, blank=True, null=True)
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    
    def __str__(self):
        size_info = f" ({self.size})" if self.size else ""
        return f'{self.product.title}{size_info} x {self.quantity}'
    
    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'


class Cart(models.Model):
    """Корзина пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Корзина {self.user.username}'
    
    def get_total_price(self):
        return sum(item.get_total() for item in self.items.all())


class CartItem(models.Model):
    """Товар в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)  # CASCADE - удалит товар из корзины
    size = models.CharField('Размер', max_length=20, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['cart', 'product', 'size']
    
    def __str__(self):
        size_info = f" ({self.size})" if self.size else ""
        return f'{self.product.title}{size_info} x {self.quantity}'
    
    def get_total(self):
        return self.product.price * self.quantity