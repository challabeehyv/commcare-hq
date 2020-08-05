# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-07-17 08:40
from __future__ import unicode_literals

import custom.icds_reports.models.aggregate
from django.db import migrations, models

from custom.icds_reports.utils.migrations import get_view_migrations


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0200_update_chm_ccs_view'),
    ]

    operations = [
        migrations.CreateModel(
            name='AggregateAppVersion',
            fields=[
                ('supervisor_id', models.TextField()),
                ('awc_id', models.TextField(primary_key=True, serialize=False)),
                ('month', models.DateField()),
                ('app_version', models.IntegerField(blank=True, null=True)),
                ('commcare_version', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'icds_dashboard_app_version',
            },
            bases=(models.Model, custom.icds_reports.models.aggregate.AggregateMixin),
        ),
        migrations.AlterUniqueTogether(
            name='aggregateappversion',
            unique_together=set([('month', 'supervisor_id', 'awc_id')]),
        ),
    ]
