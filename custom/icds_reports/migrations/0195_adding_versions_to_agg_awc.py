# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-05-28 10:24
from __future__ import unicode_literals

from django.db import migrations, models
from custom.icds_reports.utils.migrations import get_view_migrations


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0194_auto_20200528_1024'),
    ]

    operations = [
        migrations.RunSQL('ALTER TABLE agg_awc ADD COLUMN app_version INTEGER'),
        migrations.RunSQL('ALTER TABLE agg_awc ADD COLUMN commcare_version TEXT'),
    ]
    operations.extend(get_view_migrations())
