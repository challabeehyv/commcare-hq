# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-04-30 16:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0017_locationrelation_last_modified'),
    ]

    operations = [
        migrations.AddField(
            model_name='sqllocation',
            name='archived_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
