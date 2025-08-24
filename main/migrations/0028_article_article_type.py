# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_alter_specialoffer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='article_type',
            field=models.CharField(
                choices=[('news', 'Новости'), ('company', 'Новости компании')],
                default='news',
                max_length=20,
                verbose_name='Тип статьи'
            ),
        ),
    ]
