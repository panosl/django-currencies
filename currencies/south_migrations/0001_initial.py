# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Currency'
        db.create_table('currencies_currency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('symbol', self.gf('django.db.models.fields.CharField')(max_length=4, blank=True)),
            ('factor', self.gf('django.db.models.fields.DecimalField')(default=1.0, max_digits=30, decimal_places=10)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_base', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('currencies', ['Currency'])


    def backwards(self, orm):
        # Deleting model 'Currency'
        db.delete_table('currencies_currency')


    models = {
        'currencies.currency': {
            'Meta': {'ordering': "['name']", 'object_name': 'Currency'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'factor': ('django.db.models.fields.DecimalField', [], {'default': '1.0', 'max_digits': '30', 'decimal_places': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_base': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'})
        }
    }

    complete_apps = ['currencies']
