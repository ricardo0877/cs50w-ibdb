# Generated by Django 3.1.1 on 2021-06-24 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_auto_20210624_0050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='score_avg',
            field=models.FloatField(blank=True, max_length=32, null=True),
        ),
    ]
