from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_residentialvideo_videocomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='show_on_home',
            field=models.BooleanField(default=False, verbose_name='Показывать на главной'),
        ),
    ] 