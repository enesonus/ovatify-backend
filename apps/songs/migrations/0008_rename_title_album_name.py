# Generated by Django 4.2.7 on 2023-11-19 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0007_alter_song_version'),
    ]

    operations = [
        migrations.RenameField(
            model_name='album',
            old_name='title',
            new_name='name',
        ),
    ]
