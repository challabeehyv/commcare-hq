# -*- coding: utf-8 -*-
# Generated on 2020-03-21
from __future__ import unicode_literals
from django.db import migrations
from custom.icds_reports.utils.migrations import get_view_migrations


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0177_auto_20200406_1955'),
    ]

    operations = get_view_migrations()
