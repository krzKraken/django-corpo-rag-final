# Generated by Django 5.1 on 2024-10-14 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0003_alter_blog_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='title',
            field=models.TextField(default='title'),
            preserve_default=False,
        ),
    ]
