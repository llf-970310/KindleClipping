# Generated by Django 2.1.2 on 2019-03-12 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clipping', '0005_user_clipping_is_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='user_clipping',
            name='is_collected',
            field=models.BooleanField(default=False, verbose_name='是否收藏'),
        ),
    ]
