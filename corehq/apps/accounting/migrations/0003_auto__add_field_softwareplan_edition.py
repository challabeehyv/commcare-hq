# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'SoftwarePlan.edition'
        db.add_column(u'accounting_softwareplan', 'edition', self.gf('django.db.models.fields.CharField')(default='enterprise', max_length=25), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'SoftwarePlan.edition'
        db.delete_column(u'accounting_softwareplan', 'edition')


    models = {
        u'accounting.billingaccount': {
            'Meta': {'object_name': 'BillingAccount'},
            'account_type': ('django.db.models.fields.CharField', [], {'default': "'CONTRACT'", 'max_length': '25'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Currency']"}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_auto_invoiceable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'salesforce_account_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'web_user_contact': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True'})
        },
        u'accounting.billingrecord': {
            'Meta': {'object_name': 'BillingRecord'},
            'date_emailed': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'emailed_to': ('django.db.models.fields.CharField', [], {'max_length': '254', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Invoice']"}),
            'pdf_data_id': ('django.db.models.fields.CharField', [], {'max_length': '48'})
        },
        u'accounting.creditadjustment': {
            'Meta': {'object_name': 'CreditAdjustment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': "'0.0000'", 'max_digits': '10', 'decimal_places': '4'}),
            'credit_line': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.CreditLine']"}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Invoice']", 'null': 'True'}),
            'line_item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.LineItem']", 'null': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'default': "'MANUAL'", 'max_length': '25'})
        },
        u'accounting.creditline': {
            'Meta': {'object_name': 'CreditLine'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.BillingAccount']"}),
            'balance': ('django.db.models.fields.DecimalField', [], {'default': "'0.0000'", 'max_digits': '10', 'decimal_places': '4'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feature_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.FeatureRate']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.SoftwareProductRate']", 'null': 'True', 'blank': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Subscription']", 'null': 'True', 'blank': 'True'})
        },
        u'accounting.currency': {
            'Meta': {'object_name': 'Currency'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'date_updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'db_index': 'True'}),
            'rate_to_default': ('django.db.models.fields.DecimalField', [], {'default': '1.0', 'max_digits': '20', 'decimal_places': '9'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'accounting.defaultproductplan': {
            'Meta': {'object_name': 'DefaultProductPlan'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.SoftwarePlan']"}),
            'product_type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'})
        },
        u'accounting.feature': {
            'Meta': {'object_name': 'Feature'},
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        u'accounting.featurerate': {
            'Meta': {'object_name': 'FeatureRate'},
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Feature']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'monthly_fee': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '10', 'decimal_places': '2'}),
            'monthly_limit': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'per_excess_fee': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '10', 'decimal_places': '2'})
        },
        u'accounting.invoice': {
            'Meta': {'object_name': 'Invoice'},
            'balance': ('django.db.models.fields.DecimalField', [], {'default': "'0.0000'", 'max_digits': '10', 'decimal_places': '4'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_due': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'date_end': ('django.db.models.fields.DateField', [], {}),
            'date_paid': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_received': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Subscription']"}),
            'tax_rate': ('django.db.models.fields.DecimalField', [], {'default': "'0.0000'", 'max_digits': '10', 'decimal_places': '4'})
        },
        u'accounting.lineitem': {
            'Meta': {'object_name': 'LineItem'},
            'base_cost': ('django.db.models.fields.DecimalField', [], {'default': "'0.0000'", 'max_digits': '10', 'decimal_places': '4'}),
            'base_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feature_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.FeatureRate']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Invoice']"}),
            'product_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.SoftwareProductRate']", 'null': 'True'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'unit_cost': ('django.db.models.fields.DecimalField', [], {'default': "'0.0000'", 'max_digits': '10', 'decimal_places': '4'}),
            'unit_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'accounting.softwareplan': {
            'Meta': {'object_name': 'SoftwarePlan'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'default': "'enterprise'", 'max_length': '25'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'INTERNAL'", 'max_length': '10'})
        },
        u'accounting.softwareplanversion': {
            'Meta': {'object_name': 'SoftwarePlanVersion'},
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feature_rates': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['accounting.FeatureRate']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.SoftwarePlan']"}),
            'product_rates': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['accounting.SoftwareProductRate']", 'symmetrical': 'False', 'blank': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_prbac.Role']"})
        },
        u'accounting.softwareproduct': {
            'Meta': {'object_name': 'SoftwareProduct'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'product_type': ('django.db.models.fields.CharField', [], {'max_length': '25', 'db_index': 'True'})
        },
        u'accounting.softwareproductrate': {
            'Meta': {'object_name': 'SoftwareProductRate'},
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'monthly_fee': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '10', 'decimal_places': '2'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.SoftwareProduct']"})
        },
        u'accounting.subscriber': {
            'Meta': {'object_name': 'Subscriber'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'db_index': 'True'})
        },
        u'accounting.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.BillingAccount']"}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_delay_invoicing': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'plan_version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.SoftwarePlanVersion']"}),
            'salesforce_contract_id': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.Subscriber']"})
        },
        u'django_prbac.role': {
            'Meta': {'object_name': 'Role'},
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'parameters': ('django_prbac.fields.StringSetField', [], {'default': '[]', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['accounting']
