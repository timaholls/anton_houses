# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_gallery_video_thumbnail'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gallery',
            name='video_file',
        ),
    ]
