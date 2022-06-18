from django.db import models
from django.conf import settings

class Clipping(models.Model):
    content = models.TextField('内容')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    location = models.CharField('书摘位置', max_length=100)

# class User(models.Model):
#     username = models.CharField('用户名', max_length=20)
#     password = models.CharField('密码', max_length=20)

class User_Clipping(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    clipping = models.ForeignKey('Clipping', on_delete=models.CASCADE)
    time = models.DateTimeField('添加时间')
    is_deleted = models.BooleanField('是否删除', default=False)
    is_collected = models.BooleanField('是否收藏', default=False)

class Book(models.Model):
    ASIN = models.CharField('ASIN', max_length=10, null=True)
    book_origin_name = models.CharField('源书名', max_length=256)
    book_name = models.CharField('书名', max_length=256)
    author = models.CharField('作者', max_length=256)
