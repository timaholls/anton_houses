from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import ResidentialComplex, ResidentialVideo


class Command(BaseCommand):
    help = 'Создает тестовые видеообзоры для ЖК'

    def handle(self, *args, **options):
        complexes = list(ResidentialComplex.objects.all()[:3])
        if not complexes:
            self.stdout.write(self.style.WARNING('Нет жилых комплексов. Создайте ЖК перед добавлением видео.'))
            return

        data = [
            {
                'title': f'Видеообзор: {complexes[0].name}',
                'residential_complex': complexes[0],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'description': '<p>Обзор инфраструктуры и благоустройства.</p>',
            },
            {
                'title': f'Экскурсия по шоу-руму: {complexes[1].name}' if len(complexes) > 1 else 'Экскурсия по шоу-руму',
                'residential_complex': complexes[1] if len(complexes) > 1 else complexes[0],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'description': '<p>Планировки и отделка квартир.</p>',
            },
            {
                'title': f'Вид с высоты: {complexes[2].name}' if len(complexes) > 2 else 'Вид с высоты',
                'residential_complex': complexes[2] if len(complexes) > 2 else complexes[0],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'description': '<p>Панорамные виды и окрестности.</p>',
            },
        ]

        created = []
        for item in data:
            video, is_created = ResidentialVideo.objects.get_or_create(
                title=item['title'],
                residential_complex=item['residential_complex'],
                defaults={
                    'video_url': item['video_url'],
                    'description': item['description'],
                    'published_date': timezone.now().date(),
                }
            )
            if is_created:
                created.append(video)

        # Настраиваем похожие видео между собой
        if len(created) >= 2:
            created[0].related_videos.set(created[1:])
            created[1].related_videos.set([created[0]])

        self.stdout.write(self.style.SUCCESS(f'Создано видео: {len(created)}')) 