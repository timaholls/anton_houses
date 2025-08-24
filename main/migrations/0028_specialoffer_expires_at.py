# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_alter_specialoffer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialoffer',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата окончания акции'),
        ),
    ]
