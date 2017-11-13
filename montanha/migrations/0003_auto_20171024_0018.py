# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-24 02:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('montanha', '0002_auto_20161119_2337'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='biggestsupplierforyear',
            options={'verbose_name': 'Biggest Supplier For Year', 'verbose_name_plural': 'Biggest Supplier For Year'},
        ),
        migrations.AlterModelOptions(
            name='perlegislator',
            options={'verbose_name': 'Per Legislator', 'verbose_name_plural': 'Per Legislator'},
        ),
        migrations.AlterModelOptions(
            name='pernature',
            options={'verbose_name': 'Per Nature', 'verbose_name_plural': 'Per Nature'},
        ),
        migrations.AlterModelOptions(
            name='pernaturebymonth',
            options={'verbose_name': 'Per Nature By Month', 'verbose_name_plural': 'Per Nature By Month'},
        ),
        migrations.AlterModelOptions(
            name='pernaturebyyear',
            options={'verbose_name': 'Per Nature By Year', 'verbose_name_plural': 'Per Nature By Year'},
        ),
        migrations.AlterField(
            model_name='pernature',
            name='date_end',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='pernature',
            name='date_start',
            field=models.DateField(db_index=True),
        ),
    ]