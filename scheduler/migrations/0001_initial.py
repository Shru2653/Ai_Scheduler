# Generated by Django 5.2 on 2025-04-25 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('arrival_time', models.IntegerField()),
                ('burst_time', models.IntegerField()),
                ('priority', models.IntegerField()),
            ],
        ),
    ]
