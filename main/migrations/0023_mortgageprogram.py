from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_article_show_on_home'),
    ]

    operations = [
        migrations.CreateModel(
            name='MortgageProgram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Название программы')),
                ('rate', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Ставка, % годовых')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Ипотечная программа',
                'verbose_name_plural': 'Ипотечные программы',
                'ordering': ['rate', 'name'],
            },
        ),
    ] 