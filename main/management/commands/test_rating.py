"""
Management команда для проверки количества ЖК с рейтингом 4 и 5
"""
from django.core.management.base import BaseCommand
from main.services.mongo_service import get_mongo_connection


class Command(BaseCommand):
    help = 'Проверяет количество ЖК с рейтингом 4 и 5'

    def handle(self, *args, **options):
        try:
            db = get_mongo_connection()
            unified_collection = db['unified_houses_3']
            
            self.stdout.write("=" * 60)
            self.stdout.write(self.style.SUCCESS("ПРОВЕРКА ЖК С РЕЙТИНГОМ 4 И 5"))
            self.stdout.write("=" * 60)
            
            # 1. Всего ЖК в базе
            total = unified_collection.count_documents({})
            self.stdout.write(f"\n1. Всего ЖК в базе: {total}")
            
            # 2. ЖК с is_featured = True
            featured_total = unified_collection.count_documents({'is_featured': True})
            self.stdout.write(f"2. ЖК с is_featured = True: {featured_total}")
            
            # 3. ЖК с рейтингом (любым)
            with_rating = unified_collection.count_documents({'rating': {'$exists': True}})
            self.stdout.write(f"3. ЖК с рейтингом (любым): {with_rating}")
            
            # 4. ЖК с рейтингом 4 или 5
            rating_4_5 = unified_collection.count_documents({'rating': {'$in': [4, 5]}})
            self.stdout.write(f"4. ЖК с рейтингом 4 или 5: {rating_4_5}")
            
            # 5. ЖК с рейтингом 4
            rating_4 = unified_collection.count_documents({'rating': 4})
            self.stdout.write(f"5. ЖК с рейтингом 4: {rating_4}")
            
            # 6. ЖК с рейтингом 5
            rating_5 = unified_collection.count_documents({'rating': 5})
            self.stdout.write(f"6. ЖК с рейтингом 5: {rating_5}")
            
            # 7. ЖК с is_featured = True И рейтингом 4 или 5
            featured_with_rating = unified_collection.count_documents({
                'is_featured': True,
                'rating': {'$in': [4, 5], '$exists': True}
            })
            self.stdout.write(f"\n7. ЖК с is_featured=True И рейтингом 4 или 5: {featured_with_rating}")
            
            # 8. Детальная информация о ЖК с рейтингом 4 или 5
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ЖК С РЕЙТИНГОМ 4 И 5"))
            self.stdout.write("=" * 60)
            
            complexes = list(unified_collection.find({
                'is_featured': True,
                'rating': {'$in': [4, 5], '$exists': True}
            }).limit(20))
            
            self.stdout.write(f"\nНайдено ЖК (первые 20): {len(complexes)}\n")
            
            for i, comp in enumerate(complexes, 1):
                comp_id = str(comp.get('_id'))
                rating = comp.get('rating')
                is_featured = comp.get('is_featured', False)
                
                # Получаем название ЖК
                name = 'Без названия'
                if 'development' in comp and 'avito' not in comp:
                    name = (comp.get('development', {}) or {}).get('name', 'Без названия')
                else:
                    avito_name = (comp.get('avito', {}) or {}).get('development', {}) or {}
                    domclick_name = (comp.get('domclick', {}) or {}).get('development', {}) or {}
                    name = avito_name.get('name') or domclick_name.get('complex_name') or 'Без названия'
                
                self.stdout.write(f"{i}. ID: {comp_id[:24]}... | Рейтинг: {rating} | Featured: {is_featured} | Название: {name}")
            
            # 9. Распределение по рейтингам для featured ЖК
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("РАСПРЕДЕЛЕНИЕ РЕЙТИНГОВ ДЛЯ FEATURED ЖК"))
            self.stdout.write("=" * 60)
            
            for rating_val in [1, 2, 3, 4, 5]:
                count = unified_collection.count_documents({
                    'is_featured': True,
                    'rating': rating_val
                })
                self.stdout.write(f"Рейтинг {rating_val}: {count} ЖК")
            
            # 10. Featured ЖК без рейтинга
            no_rating = unified_collection.count_documents({
                'is_featured': True,
                'rating': {'$exists': False}
            })
            self.stdout.write(f"Без рейтинга: {no_rating} ЖК")
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("ВЫВОДЫ"))
            self.stdout.write("=" * 60)
            self.stdout.write(f"Для отображения на главной странице доступно: {featured_with_rating} ЖК")
            if featured_with_rating < 9:
                self.stdout.write(self.style.WARNING(
                    f"⚠️  ВНИМАНИЕ: Доступно только {featured_with_rating} ЖК, а нужно 9!"
                ))
                self.stdout.write(self.style.WARNING(
                    f"   Необходимо проставить рейтинг 4 или 5 еще {9 - featured_with_rating} ЖК"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Достаточно ЖК для отображения (нужно 9, есть {featured_with_rating})"
                ))
            
        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f"\n❌ ОШИБКА: {e}"))
            self.stdout.write(traceback.format_exc())

