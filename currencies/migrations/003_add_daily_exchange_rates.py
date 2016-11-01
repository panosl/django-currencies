# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('currencies', '0002_alter_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyCurrencyExchangeRate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('factor', models.DecimalField(default=1.0, help_text='Specifies the difference of the currency to default one.', verbose_name='factor', max_digits=30, decimal_places=10)),
                ('date', models.DateField(db_index=True)),
                ('currency', models.ForeignKey(to='currencies.Currency')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='currency',
            name='code',
            field=models.CharField(max_length=3, verbose_name='code', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='currency',
            name='name',
            field=models.CharField(max_length=35, verbose_name='name', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='currency',
            unique_together=set([('code', 'name')]),
        ),
    ]
