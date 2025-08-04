from django.core.management.base import BaseCommand
from main.models import CompanyInfo

class Command(BaseCommand):
    help = 'Создает начальную информацию о компании'

    def handle(self, *args, **options):
        # Проверяем, существует ли уже информация о компании
        if CompanyInfo.objects.exists():
            self.stdout.write(
                self.style.WARNING('Информация о компании уже существует!')
            )
            return

        # Создаем информацию о компании
        company_info = CompanyInfo.objects.create(
            founder_name='Антон Бакметов',
            founder_position='основатель компании',
            company_name='Антон Хаус',
            quote='Помогаем клиентам найти идеальную квартиру в современных жилых комплексах, предоставляя полное сопровождение сделки и консультации по всем вопросам недвижимости',
            description='Компания Антон Хаус специализируется на продаже квартир в лучших жилых комплексах. Мы предоставляем полное сопровождение сделки и консультации по всем вопросам недвижимости.',
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'Создана информация о компании: {company_info.company_name}')
        )
        self.stdout.write(
            self.style.SUCCESS('Теперь вы можете загрузить фото основателя через админку Django')
        ) 