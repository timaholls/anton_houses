/**
 * Диагностический скрипт для проверки формата цен в API квартир
 * 
 * Использование:
 * 1. Откройте консоль браузера (F12)
 * 2. Скопируйте и вставьте этот код
 * 3. Запустите функцию checkApartmentPrices()
 * 
 * Или используйте в консоли:
 * checkApartmentPrices('price_asc', 15)
 */

async function checkApartmentPrices(sort = 'price_asc', perPage = 15) {
    console.log('='.repeat(80));
    console.log('🔍 ДИАГНОСТИКА ЦЕН В API КВАРТИР');
    console.log('='.repeat(80));
    
    try {
        // Делаем запрос к API квартир
        const url = `/api/apartments/?per_page=${perPage}&sort=${sort}`;
        console.log(`\n📡 Запрос: ${url}`);
        
        const response = await fetch(url);
        const data = await response.json();
        
        console.log(`\n✅ Ответ получен:`);
        console.log(`   Всего квартир: ${data.total_count || 0}`);
        console.log(`   На странице: ${data.apartments?.length || 0}`);
        
        if (!data.apartments || data.apartments.length === 0) {
            console.log('\n❌ Квартиры не найдены');
            return;
        }
        
        console.log('\n' + '='.repeat(80));
        console.log('📊 АНАЛИЗ ЦЕН КВАРТИР:');
        console.log('='.repeat(80));
        
        // Анализируем первые N квартир
        const apartments = data.apartments.slice(0, Math.min(10, data.apartments.length));
        
        apartments.forEach((apt, index) => {
            console.log(`\n${index + 1}. Квартира ID: ${apt.id || 'N/A'}`);
            console.log(`   Название: ${apt.apartment_title || apt.title || 'N/A'}`);
            console.log(`   ЖК: ${apt.complex_name || 'N/A'}`);
            
            // Анализируем цену
            console.log(`   📍 ПОЛЕ "price": ${JSON.stringify(apt.price)} (тип: ${typeof apt.price})`);
            console.log(`   📍 ПОЛЕ "price_display": ${JSON.stringify(apt.price_display)} (тип: ${typeof apt.price_display})`);
            console.log(`   📍 ПОЛЕ "price_range": ${JSON.stringify(apt.price_range)} (тип: ${typeof apt.price_range})`);
            console.log(`   📍 ПОЛЕ "price_num": ${JSON.stringify(apt.price_num)} (тип: ${typeof apt.price_num})`);
            
            // Пытаемся понять формат
            let priceAnalysis = '';
            if (apt.price_num !== undefined && apt.price_num !== null) {
                priceAnalysis = `✅ price_num = ${apt.price_num} (${typeof apt.price_num})`;
                if (typeof apt.price_num === 'number') {
                    if (apt.price_num < 100) {
                        priceAnalysis += ' → Похоже на МИЛЛИОНЫ';
                    } else {
                        priceAnalysis += ' → Похоже на РУБЛИ';
                    }
                }
            } else {
                priceAnalysis = '❌ price_num отсутствует или null';
            }
            console.log(`   💰 АНАЛИЗ: ${priceAnalysis}`);
            
            // Показываем все поля для отладки
            console.log(`   📦 Все поля с "price":`, Object.keys(apt).filter(k => k.toLowerCase().includes('price')));
        });
        
        console.log('\n' + '='.repeat(80));
        console.log('📈 СТАТИСТИКА ПО ЦЕНАМ:');
        console.log('='.repeat(80));
        
        const prices = data.apartments
            .map(apt => apt.price_num)
            .filter(p => p !== undefined && p !== null && typeof p === 'number');
        
        if (prices.length > 0) {
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
            
            console.log(`   Минимальная цена (price_num): ${minPrice}`);
            console.log(`   Максимальная цена (price_num): ${maxPrice}`);
            console.log(`   Средняя цена (price_num): ${avgPrice.toFixed(2)}`);
            
            // Определяем формат
            if (maxPrice < 100) {
                console.log(`   ✅ Формат: МИЛЛИОНЫ рублей (все значения < 100)`);
            } else if (minPrice > 1000) {
                console.log(`   ✅ Формат: РУБЛИ (все значения > 1000)`);
            } else {
                console.log(`   ⚠️  Формат: СМЕШАННЫЙ или НЕОПРЕДЕЛЕННЫЙ`);
            }
            
            // Показываем первые 5 значений
            console.log(`\n   Первые 5 значений price_num:`, prices.slice(0, 5));
        } else {
            console.log('   ❌ Нет валидных значений price_num');
        }
        
        console.log('\n' + '='.repeat(80));
        console.log('🧪 ТЕСТ ФИЛЬТРАЦИИ:');
        console.log('='.repeat(80));
        
        // Тестируем фильтр "до 2 000 000"
        const filterValue = 2000000;
        const filterValueMillions = filterValue / 1000000; // 2.0
        
        console.log(`\n   Тест фильтра "до ${filterValue.toLocaleString('ru-RU')} ₽":`);
        console.log(`   Конвертированное значение: ${filterValueMillions} млн`);
        
        const filtered = data.apartments.filter(apt => {
            if (apt.price_num === undefined || apt.price_num === null) return false;
            return apt.price_num <= filterValueMillions;
        });
        
        console.log(`   Квартир до ${filterValue.toLocaleString('ru-RU')} ₽: ${filtered.length} из ${data.apartments.length}`);
        
        if (filtered.length > 0) {
            console.log(`   Примеры отфильтрованных квартир:`);
            filtered.slice(0, 3).forEach((apt, i) => {
                console.log(`     ${i + 1}. price_num=${apt.price_num}, price=${apt.price}`);
            });
        }
        
        console.log('\n' + '='.repeat(80));
        console.log('✅ Диагностика завершена');
        console.log('='.repeat(80));
        
        return data;
        
    } catch (error) {
        console.error('❌ Ошибка при запросе:', error);
        return null;
    }
}

// Дополнительная функция для тестирования с фильтром
async function testPriceFilter(priceTo, sort = 'price_asc', perPage = 15) {
    console.log('='.repeat(80));
    console.log(`🧪 ТЕСТ ФИЛЬТРА "до ${priceTo.toLocaleString('ru-RU')} ₽"`);
    console.log('='.repeat(80));
    
    try {
        // Делаем запрос с фильтром
        const url = `/api/apartments/?per_page=${perPage}&sort=${sort}&price_to=${priceTo}`;
        console.log(`\n📡 Запрос: ${url}`);
        
        const response = await fetch(url);
        const data = await response.json();
        
        console.log(`\n✅ Ответ получен:`);
        console.log(`   Всего квартир: ${data.total_count || 0}`);
        console.log(`   На странице: ${data.apartments?.length || 0}`);
        
        if (data.apartments && data.apartments.length > 0) {
            console.log(`\n   Первые 5 квартир:`);
            data.apartments.slice(0, 5).forEach((apt, i) => {
                console.log(`   ${i + 1}. price_num=${apt.price_num}, price=${apt.price}, title=${apt.apartment_title}`);
            });
            
            // Проверяем, все ли квартиры действительно <= фильтра
            const priceToMillions = priceTo >= 100 ? priceTo / 1000000 : priceTo;
            const invalid = data.apartments.filter(apt => apt.price_num > priceToMillions);
            
            if (invalid.length > 0) {
                console.log(`\n   ⚠️  НАЙДЕНЫ НЕКОРРЕКТНЫЕ РЕЗУЛЬТАТЫ (${invalid.length}):`);
                invalid.slice(0, 5).forEach((apt, i) => {
                    console.log(`   ${i + 1}. price_num=${apt.price_num} > ${priceToMillions} (фильтр)`);
                });
            } else {
                console.log(`\n   ✅ Все квартиры соответствуют фильтру`);
            }
        }
        
        return data;
        
    } catch (error) {
        console.error('❌ Ошибка при запросе:', error);
        return null;
    }
}

// Экспортируем функции для использования в консоли
if (typeof window !== 'undefined') {
    window.checkApartmentPrices = checkApartmentPrices;
    window.testPriceFilter = testPriceFilter;
    console.log('✅ Диагностические функции загружены:');
    console.log('   - checkApartmentPrices(sort, perPage)');
    console.log('   - testPriceFilter(priceTo, sort, perPage)');
    console.log('\nПримеры использования:');
    console.log('   checkApartmentPrices()');
    console.log('   checkApartmentPrices("price_asc", 20)');
    console.log('   testPriceFilter(2000000)');
}

