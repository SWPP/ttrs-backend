# Generated by Django 2.0.4 on 2018-05-03 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0004_auto_20180502_2205'),
    ]

    operations = [
        migrations.AddField(
            model_name='crawler',
            name='semester',
            field=models.CharField(default='', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crawler',
            name='year',
            field=models.CharField(default='', max_length=10),
            preserve_default=False,
        ),
    ]
