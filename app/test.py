import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from backend.models import Category, Product


for dir in os.listdir('backend/images'):
    title = dir.removesuffix('.jpg')
    path = 'backend/images/' + dir
    Product.products.create(title=title, description='', image=path, price=400, category=Category.categories.first())
