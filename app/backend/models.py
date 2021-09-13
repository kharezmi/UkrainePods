from django.db import models
from django.db.models import F, Sum


class BotUser(models.Model):
    class Lang(models.TextChoices):
        RU = 'ru'
        UA = 'ua'

    chat_id = models.IntegerField(unique=True)
    full_name = models.CharField(max_length=255)
    lang = models.CharField(max_length=2)
    bot_state = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.chat_id)


class Category(models.Model):
    categories = models.Manager()
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        to="self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    products = models.Manager()

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        to=Category,
        on_delete=models.CASCADE,
        related_name='products',
    )
    price = models.FloatField()
    image = models.ImageField(upload_to='backend/images')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def price(self):
        return self.product.price * self.count


class ShopCard(models.Model):
    shop_cards = models.Manager()
    user = models.OneToOneField(
        to=BotUser,
        on_delete=models.CASCADE,
        related_name='shop_card',
    )
    purchases = models.ManyToManyField(Purchase)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def price(self):
        price = self.purchases.aggregate(
            price_all=Sum(F('product__price')*F('count'))
        )['price_all']
        if not price:
            price = 0

        return price


class Order(models.Model):
    orders = models.Manager()
    user = models.ForeignKey(
        to=BotUser,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    purchases = models.ManyToManyField(Purchase)

    full_name = models.CharField(max_length=255, null=True)
    contact = models.CharField(max_length=15, null=True)
    mail = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)

    completed = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}. {self.user}'


class Review(models.Model):
    reviews = models.Manager()
    user = models.OneToOneField(
        to=BotUser,
        on_delete=models.CASCADE,
        related_name='shop_review',
    )
    rating = models.IntegerField()
    description = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated']

    def __str__(self):
        return str(self.rating)


class KeyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='Key')


class MessageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='Message')


class SmileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='Smile')


class Template(models.Model):
    class Type(models.TextChoices):
        KEY = 'Key'
        MESSAGE = 'Message'
        SMILE = 'Smile'

    templates = models.Manager()
    keys = KeyManager()
    messages = MessageManager()
    smiles = SmileManager()

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=Type.choices)
    body_ru = models.TextField()
    body_ua = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)

        keys = Template.keys.all()
        messages = Template.messages.all()
        smiles = Template.smiles.all()
        with open('backend/templates.py', 'w') as file:
            file.write('from .models import Template\n\n')
            file.write('\n')
            file.write('keys = Template.keys.all()\n')
            file.write('messages = Template.messages.all()\n')
            file.write('smiles = Template.smiles.all()\n\n')
            file.write('\n')
            file.write('class Keys():\n')
            for index, key in enumerate(keys):
                file.write(f'    {key.title} = keys[{index}]\n')

            file.write('\n\n')
            file.write('class Messages():\n')
            for index, message in enumerate(messages):
                file.write(f'    {message.title} = messages[{index}]\n')

            file.write('\n\n')
            file.write('class Smiles():\n')
            for index, smile in enumerate(smiles):
                file.write(f'    {smile.title} = smiles[{index}]\n')

        return result

    @property
    def text(self):
        return self.body_ru

    def get(self, lang):
        return getattr(self, f'body_{lang}')

    def getall(self):
        return (self.body_ru, self.body_ua)

    def format(self, **kwargs):
        return self.body_ru.format(**kwargs)

    def __format__(self, format_spec):
        return format(self.body_ru, format_spec)

    def __str__(self):
        return self.title
