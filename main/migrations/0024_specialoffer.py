from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_mortgageprogram'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialOffer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок акции')),
                ('description', models.TextField(verbose_name='Описание акции')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('priority', models.IntegerField(default=0, verbose_name='Приоритет')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создана')),
                ('residential_complex', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers', to='main.residentialcomplex', verbose_name='Жилой комплекс')),
            ],
            options={
                'verbose_name': 'Акция',
                'verbose_name_plural': 'Акции',
                'ordering': ['-priority', '-created_at'],
            },
        ),
    ] 