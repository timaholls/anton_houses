from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import BranchOffice, Employee, ResidentialComplex, SecondaryProperty
import random


class Command(BaseCommand):
    help = 'Создает полный набор данных: офисы, сотрудников, жилые комплексы и вторичную недвижимость'

    def add_arguments(self, parser):
        parser.add_argument(
            '--offices',
            type=int,
            default=3,
            help='Количество офисов для создания'
        )
        parser.add_argument(
            '--employees',
            type=int,
            default=10,
            help='Количество сотрудников для создания'
        )
        parser.add_argument(
            '--residential',
            type=int,
            default=20,
            help='Количество жилых комплексов для создания'
        )
        parser.add_argument(
            '--secondary',
            type=int,
            default=20,
            help='Количество объектов вторичной недвижимости для создания'
        )

    def handle(self, *args, **options):
        offices_count = options['offices']
        employees_count = options['employees']
        residential_count = options['residential']
        secondary_count = options['secondary']

        self.stdout.write('🏢 Создаю офисы...')
        offices = self.create_offices(offices_count)

        self.stdout.write('👥 Создаю сотрудников...')
        employees = self.create_employees(employees_count, offices)

        self.stdout.write('🏠 Создаю жилые комплексы...')
        self.create_residential_complexes(residential_count, employees)

        self.stdout.write('🏘️ Создаю вторичную недвижимость...')
        self.create_secondary_properties(secondary_count, employees)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Все данные успешно созданы!\n'
                f'Создано:\n'
                f'- Офисов: {offices_count}\n'
                f'- Сотрудников: {employees_count}\n'
                f'- Жилых комплексов: {residential_count}\n'
                f'- Объектов вторичной недвижимости: {secondary_count}\n'
                f'\nВсе объекты привязаны к агентам, агенты - к офисам.'
            )
        )

    def create_offices(self, count):
        """Создает офисы"""
        offices_data = [
            {
                'name': 'Главный офис CENTURY 21',
                'city': 'Уфа',
                'address': 'ул. Ленина, 1',
                'phone': '+7 (347) 201-94-78',
                'email': 'info@century21.ru',
                'schedule': 'Пн-Пт: 9:00-18:00, Сб: 10:00-16:00'
            },
            {
                'name': 'Офис продаж "Центральный"',
                'city': 'Уфа',
                'address': 'ул. Пушкина, 15',
                'phone': '+7 (347) 234-56-78',
                'email': 'central@century21.ru',
                'schedule': 'Пн-Пт: 9:00-19:00, Сб-Вс: 10:00-17:00'
            },
            {
                'name': 'Офис продаж "Северный"',
                'city': 'Уфа',
                'address': 'ул. Гагарина, 25',
                'phone': '+7 (347) 345-67-89',
                'email': 'north@century21.ru',
                'schedule': 'Пн-Пт: 8:00-18:00, Сб: 9:00-15:00'
            },
            {
                'name': 'Офис продаж "Южный"',
                'city': 'Уфа',
                'address': 'ул. Менделеева, 8',
                'phone': '+7 (347) 456-78-90',
                'email': 'south@century21.ru',
                'schedule': 'Пн-Пт: 9:00-18:00, Сб: 10:00-16:00'
            },
            {
                'name': 'Офис продаж "Западный"',
                'city': 'Уфа',
                'address': 'ул. Революционная, 12',
                'phone': '+7 (347) 567-89-01',
                'email': 'west@century21.ru',
                'schedule': 'Пн-Пт: 9:00-19:00, Сб: 10:00-17:00'
            }
        ]

        offices = []
        for i in range(min(count, len(offices_data))):
            office_data = offices_data[i]
            office = BranchOffice.objects.create(**office_data)
            offices.append(office)
            self.stdout.write(f'✅ Создан офис: {office.name}')

        return offices

    def create_employees(self, count, offices):
        """Создает сотрудников"""
        employees_data = [
            {
                'full_name': 'Иванов Иван Иванович',
                'position': 'Руководитель офиса',
                'experience_years': 8,
                'description': '<p>Опытный специалист с многолетним стажем работы в сфере недвижимости. Специализируется на работе с премиальными объектами и VIP-клиентами.</p>',
                'achievements': '<ul><li>Более 500 успешных сделок</li><li>Лучший агент года 2023</li><li>Сертификат "Эксперт по премиальной недвижимости"</li></ul>',
                'specializations': 'Премиальная недвижимость, элитные новостройки, загородная недвижимость',
                'phone': '+7 (347) 123-45-67',
                'email': 'ivanov@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Петрова Анна Сергеевна',
                'position': 'Агент по недвижимости',
                'experience_years': 5,
                'description': '<p>Профессиональный агент с глубоким знанием рынка недвижимости Уфы. Помогает клиентам найти идеальное жилье.</p>',
                'achievements': '<ul><li>Более 200 успешных сделок</li><li>Специалист по ипотечному кредитованию</li><li>Награда "Лучший дебют года"</li></ul>',
                'specializations': 'Ипотечное кредитование, новостройки, вторичная недвижимость',
                'phone': '+7 (347) 234-56-78',
                'email': 'petrova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Сидоров Дмитрий Алексеевич',
                'position': 'Агент по недвижимости',
                'experience_years': 6,
                'description': '<p>Эксперт по коммерческой недвижимости и инвестиционным проектам. Помогает инвесторам найти выгодные объекты.</p>',
                'achievements': '<ul><li>Более 150 коммерческих сделок</li><li>Сертификат по инвестиционной недвижимости</li><li>Эксперт по оценке недвижимости</li></ul>',
                'specializations': 'Коммерческая недвижимость, инвестиционные проекты, оценка недвижимости',
                'phone': '+7 (347) 345-67-89',
                'email': 'sidorov@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Козлова Елена Викторовна',
                'position': 'Специалист по ипотеке',
                'experience_years': 7,
                'description': '<p>Специалист по ипотечному кредитованию с опытом работы в банковской сфере. Помогает клиентам выбрать оптимальную ипотечную программу.</p>',
                'achievements': '<ul><li>Более 300 одобренных ипотечных заявок</li><li>Сертификат "Ипотечный консультант"</li><li>Партнерские отношения с ведущими банками</li></ul>',
                'specializations': 'Ипотечное кредитование, банковские продукты, консультации по кредитам',
                'phone': '+7 (347) 456-78-90',
                'email': 'kozlova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Морозов Александр Петрович',
                'position': 'Агент по недвижимости',
                'experience_years': 4,
                'description': '<p>Молодой и энергичный специалист, специализирующийся на работе с молодыми семьями и первыми покупателями.</p>',
                'achievements': '<ul><li>Более 100 сделок с молодыми семьями</li><li>Специалист по государственным программам</li><li>Эксперт по новостройкам</li></ul>',
                'specializations': 'Новостройки, государственные программы, работа с молодыми семьями',
                'phone': '+7 (347) 567-89-01',
                'email': 'morozov@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Новикова Ольга Дмитриевна',
                'position': 'Агент по недвижимости',
                'experience_years': 9,
                'description': '<p>Опытный агент с глубоким знанием всех районов Уфы. Специализируется на вторичной недвижимости и сделках с недвижимостью.</p>',
                'achievements': '<ul><li>Более 400 сделок с вторичной недвижимостью</li><li>Эксперт по юридическим аспектам сделок</li><li>Сертификат "Профессиональный оценщик"</li></ul>',
                'specializations': 'Вторичная недвижимость, юридическое сопровождение, оценка недвижимости',
                'phone': '+7 (347) 678-90-12',
                'email': 'novikova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Волков Сергей Николаевич',
                'position': 'Агент по недвижимости',
                'experience_years': 3,
                'description': '<p>Специалист по загородной недвижимости и коттеджным поселкам. Помогает клиентам найти идеальный дом за городом.</p>',
                'achievements': '<ul><li>Более 50 сделок с загородной недвижимостью</li><li>Специалист по коттеджным поселкам</li><li>Эксперт по земельным участкам</li></ul>',
                'specializations': 'Загородная недвижимость, коттеджные поселки, земельные участки',
                'phone': '+7 (347) 789-01-23',
                'email': 'volkov@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Смирнова Мария Александровна',
                'position': 'Агент по недвижимости',
                'experience_years': 6,
                'description': '<p>Специалист по элитной недвижимости и пентхаусам. Работает с требовательными клиентами премиум-сегмента.</p>',
                'achievements': '<ul><li>Более 80 сделок с элитной недвижимостью</li><li>Сертификат "Элитная недвижимость"</li><li>Эксперт по пентхаусам</li></ul>',
                'specializations': 'Элитная недвижимость, пентхаусы, премиум-сегмент',
                'phone': '+7 (347) 890-12-34',
                'email': 'smirnova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Лебедев Андрей Владимирович',
                'position': 'Агент по недвижимости',
                'experience_years': 5,
                'description': '<p>Специалист по инвестиционной недвижимости. Помогает клиентам создать пассивный доход через недвижимость.</p>',
                'achievements': '<ul><li>Более 120 инвестиционных сделок</li><li>Сертификат "Инвестиционная недвижимость"</li><li>Эксперт по доходности объектов</li></ul>',
                'specializations': 'Инвестиционная недвижимость, доходность, пассивный доход',
                'phone': '+7 (347) 901-23-45',
                'email': 'lebedev@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Кузнецова Татьяна Игоревна',
                'position': 'Агент по недвижимости',
                'experience_years': 7,
                'description': '<p>Специалист по работе с иностранными клиентами и экспатами. Помогает адаптироваться к российскому рынку недвижимости.</p>',
                'achievements': '<ul><li>Более 90 сделок с иностранными клиентами</li><li>Сертификат "Международная недвижимость"</li><li>Владение английским и немецким языками</li></ul>',
                'specializations': 'Международная недвижимость, работа с экспатами, иностранные клиенты',
                'phone': '+7 (347) 012-34-56',
                'email': 'kuznetsova@century21.ru',
                'is_featured': True
            }
        ]

        employees = []
        for i in range(min(count, len(employees_data))):
            employee_data = employees_data[i].copy()
            employee_data['branch'] = random.choice(offices)
            employee = Employee.objects.create(**employee_data)
            employees.append(employee)
            self.stdout.write(f'✅ Создан сотрудник: {employee.full_name} ({employee.branch.name})')

        return employees

    def create_residential_complexes(self, count, employees):
        """Создает жилые комплексы"""
        complexes_data = [
            {'name': 'ЖК "Солнечный"', 'price_from': 3.2, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Солнечная, 15'},
            {'name': 'ЖК "Зеленый"', 'price_from': 4.1, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Зеленая, 8'},
            {'name': 'ЖК "Речной"', 'price_from': 3.8, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Речная, 22'},
            {'name': 'ЖК "Горный"', 'price_from': 5.2, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Горная, 12'},
            {'name': 'ЖК "Лесной"', 'price_from': 3.5, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Лесная, 45'},
            {'name': 'ЖК "Морской"', 'price_from': 4.8, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Морская, 33'},
            {'name': 'ЖК "Небесный"', 'price_from': 6.1, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Небесная, 7'},
            {'name': 'ЖК "Звездный"', 'price_from': 4.3, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Звездная, 18'},
            {'name': 'ЖК "Лунный"', 'price_from': 3.9, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Лунная, 25'},
            {'name': 'ЖК "Солнечный-2"', 'price_from': 4.5, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Солнечная, 28'},
            {'name': 'ЖК "Парковый"', 'price_from': 5.7, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Парковая, 11'},
            {'name': 'ЖК "Садовый"', 'price_from': 3.7, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Садовая, 14'},
            {'name': 'ЖК "Центральный"', 'price_from': 7.2, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Центральная, 3'},
            {'name': 'ЖК "Северный"', 'price_from': 4.0, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Северная, 19'},
            {'name': 'ЖК "Южный"', 'price_from': 3.6, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Южная, 27'},
            {'name': 'ЖК "Западный"', 'price_from': 4.2, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Западная, 31'},
            {'name': 'ЖК "Восточный"', 'price_from': 3.4, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Восточная, 9'},
            {'name': 'ЖК "Премиум"', 'price_from': 8.5, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Премиумная, 5'},
            {'name': 'ЖК "Комфорт"', 'price_from': 5.8, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Комфортная, 16'},
            {'name': 'ЖК "Элитный"', 'price_from': 9.2, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Элитная, 2'}
        ]

        for i in range(min(count, len(complexes_data))):
            complex_data = complexes_data[i].copy()
            complex_data['agent'] = random.choice(employees)
            complex_data['commute_time'] = f'{random.randint(10, 45)} минут'
            complex_data['house_type'] = random.choice(['apartment', 'house', 'townhouse'])
            complex_data['house_class'] = random.choice(['economy', 'comfort', 'premium'])
            complex_data['status'] = random.choice(['construction', 'completed'])
            complex_data['is_featured'] = random.choice([True, False])
            
            complex = ResidentialComplex.objects.create(**complex_data)
            self.stdout.write(f'✅ Создан ЖК: {complex.name} (агент: {complex.agent.full_name})')

    def create_secondary_properties(self, count, employees):
        """Создает объекты вторичной недвижимости"""
        properties_data = [
            {'name': 'Квартира в центре', 'price': 4.8, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Ленина, 25'},
            {'name': 'Дом с участком', 'price': 12.5, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Садовая, 8'},
            {'name': 'Квартира с ремонтом', 'price': 3.9, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Пушкина, 12'},
            {'name': 'Таунхаус', 'price': 8.2, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Горная, 15'},
            {'name': 'Квартира в новостройке', 'price': 5.1, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Солнечная, 33'},
            {'name': 'Дом в коттеджном поселке', 'price': 15.7, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Лесная, 7'},
            {'name': 'Квартира с мебелью', 'price': 4.3, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Речная, 18'},
            {'name': 'Пентхаус', 'price': 22.5, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Небесная, 1'},
            {'name': 'Квартира в историческом центре', 'price': 6.8, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Центральная, 11'},
            {'name': 'Дом с гаражом', 'price': 18.3, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Автомобильная, 9'},
            {'name': 'Квартира с видом на парк', 'price': 5.4, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Парковая, 22'},
            {'name': 'Коттедж с бассейном', 'price': 25.1, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Премиумная, 3'},
            {'name': 'Квартира в тихом районе', 'price': 3.7, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Тихая, 14'},
            {'name': 'Дом с садом', 'price': 16.9, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Садовая, 26'},
            {'name': 'Квартира с балконом', 'price': 4.6, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Балконная, 17'},
            {'name': 'Таунхаус с террасой', 'price': 9.8, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Террасная, 5'},
            {'name': 'Квартира в элитном доме', 'price': 7.5, 'city': 'Уфа', 'district': 'Калининский', 'street': 'ул. Элитная, 8'},
            {'name': 'Дом с мансардой', 'price': 19.2, 'city': 'Уфа', 'district': 'Октябрьский', 'street': 'ул. Мансардная, 12'},
            {'name': 'Квартира с камином', 'price': 6.3, 'city': 'Уфа', 'district': 'Ленинский', 'street': 'ул. Каминная, 20'},
            {'name': 'Коттедж с зимним садом', 'price': 28.7, 'city': 'Уфа', 'district': 'Советский', 'street': 'ул. Садовая, 35'}
        ]

        for i in range(min(count, len(properties_data))):
            property_data = properties_data[i].copy()
            property_data['agent'] = random.choice(employees)
            property_data['commute_time'] = f'{random.randint(5, 40)} минут'
            property_data['house_type'] = random.choice(['apartment', 'house', 'cottage', 'townhouse'])
            property_data['area'] = random.uniform(30.0, 200.0)
            
            property_obj = SecondaryProperty.objects.create(**property_data)
            self.stdout.write(f'✅ Создан объект: {property_obj.name} (агент: {property_obj.agent.full_name})')
