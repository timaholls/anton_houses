from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import SpecialOffer


class Command(BaseCommand):
    help = 'Продлевает все активные акции на месяц от текущей даты'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Количество дней для продления (по умолчанию 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать какие акции будут обновлены без изменений'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Получаем текущую дату
        now = timezone.now()
        new_expires_at = now + timedelta(days=days)
        
        # Находим все активные акции
        active_offers = SpecialOffer.objects.filter(is_active=True)
        
        if not active_offers.exists():
            self.stdout.write(
                self.style.WARNING('Нет активных акций для продления')
            )
            return
        
        self.stdout.write(f'Найдено активных акций: {active_offers.count()}')
        self.stdout.write(f'Новая дата окончания: {new_expires_at.strftime("%d.%m.%Y %H:%M")}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Режим предварительного просмотра:'))
            for offer in active_offers:
                current_expires = offer.expires_at.strftime("%d.%m.%Y %H:%M") if offer.expires_at else "Бессрочно"
                self.stdout.write(
                    f'  - "{offer.title}" (ЖК: {offer.residential_complex.name})'
                )
                self.stdout.write(f'    Текущая дата: {current_expires}')
                self.stdout.write(f'    Новая дата: {new_expires_at.strftime("%d.%m.%Y %H:%M")}')
                self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(f'Будет обновлено {active_offers.count()} акций')
            )
            return
        
        # Обновляем акции
        updated_count = 0
        for offer in active_offers:
            old_expires = offer.expires_at
            offer.expires_at = new_expires_at
            offer.save(update_fields=['expires_at'])
            updated_count += 1
            
            self.stdout.write(
                f'✓ "{offer.title}" (ЖК: {offer.residential_complex.name})'
            )
            if old_expires:
                self.stdout.write(
                    f'  Было: {old_expires.strftime("%d.%m.%Y %H:%M")}'
                )
            else:
                self.stdout.write('  Было: Бессрочно')
            self.stdout.write(
                f'  Стало: {new_expires_at.strftime("%d.%m.%Y %H:%M")}'
            )
            self.stdout.write('')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно продлено {updated_count} акций до {new_expires_at.strftime("%d.%m.%Y %H:%M")}'
            )
        )
