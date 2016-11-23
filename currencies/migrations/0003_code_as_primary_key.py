# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('currencies', '0002_alter_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='currency',
            name='id',
        ),
        migrations.AlterField(
            model_name='currency',
            name='code',
            field=models.CharField(primary_key=True, max_length=3, verbose_name='code'),
        ),
    ]
