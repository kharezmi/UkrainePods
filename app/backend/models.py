from django.db import models


class BotUser(models.Model):
    chat_id = models.IntegerField(unique=True)
    full_name = models.CharField(max_length=255, null=True)
    contact = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

    
class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.IntegerField(verbose_name='Soni')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.FloatField()

    def __str__(self):
        return self.title


class Purchase(models.Model):
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)