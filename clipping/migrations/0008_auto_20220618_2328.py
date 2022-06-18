# Generated by Django 2.0.9 on 2022-06-18 23:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clipping', '0007_auto_20220618_1507'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='book_alias_name',
            field=models.CharField(default='', max_length=256, verbose_name='展示书名'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='book',
            name='book_name',
            field=models.CharField(max_length=256, verbose_name='源书名'),
        ),
    ]
