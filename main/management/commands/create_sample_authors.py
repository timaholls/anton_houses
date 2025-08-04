from django.core.management.base import BaseCommand
from main.models import Author, Article
from django.utils import timezone

class Command(BaseCommand):
    help = 'Создает тестовых авторов и назначает их к статьям'

    def handle(self, *args, **options):
        # Создаем авторов
        authors_data = [
            {
                'name': 'Иваткина Мария',
                'position': 'Эксперт Дирекции финансовой грамотности НИФИ Минфина России',
                'description': 'Специалист по финансовой грамотности с опытом работы более 10 лет. Автор множества статей по ипотеке и финансовому планированию.',
                'articles_count': 281,
                'total_views': 497087,
                'total_likes': 9375
            },
            {
                'name': 'Петров Александр',
                'position': 'Риелтор с 15-летним стажем',
                'description': 'Профессиональный риелтор, специализирующийся на первичном рынке недвижимости. Помог более 500 семьям найти свой дом.',
                'articles_count': 156,
                'total_views': 234567,
                'total_likes': 5432
            },
            {
                'name': 'Сидорова Елена',
                'position': 'Юрист по недвижимости',
                'description': 'Специалист по правовым вопросам в сфере недвижимости. Консультирует по вопросам сделок с недвижимостью и ипотечного кредитования.',
                'articles_count': 89,
                'total_views': 123456,
                'total_likes': 2987
            },
            {
                'name': 'Козлов Дмитрий',
                'position': 'Аналитик рынка недвижимости',
                'description': 'Аналитик с опытом работы в крупных агентствах недвижимости. Специализируется на анализе рынка и прогнозировании цен.',
                'articles_count': 67,
                'total_views': 98765,
                'total_likes': 2156
            }
        ]

        created_authors = []
        for author_data in authors_data:
            author, created = Author.objects.get_or_create(
                name=author_data['name'],
                defaults=author_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создан автор: {author.name}')
                )
            else:
                # Обновляем существующего автора
                for key, value in author_data.items():
                    setattr(author, key, value)
                author.save()
                self.stdout.write(
                    self.style.WARNING(f'Обновлен автор: {author.name}')
                )
            created_authors.append(author)

        # Назначаем авторов к статьям
        articles = Article.objects.all()
        for i, article in enumerate(articles):
            # Распределяем авторов по кругу
            author = created_authors[i % len(created_authors)]
            article.author = author
            article.save()
            self.stdout.write(
                self.style.SUCCESS(f'Назначен автор {author.name} к статье "{article.title}"')
            )

        self.stdout.write(
            self.style.SUCCESS('Успешно созданы авторы и назначены к статьям!')
        ) 