# Generated by Django 5.1.6 on 2025-02-22 13:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='password_hash',
        ),
    ]
