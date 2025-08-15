from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_specialoffer'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialoffer',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='offers/', verbose_name='Изображение'),
        ),
    ] 