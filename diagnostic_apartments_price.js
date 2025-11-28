/**
 * Диагностический скрипт для проверки фильтрации квартир по цене
 * 
 * Использование в консоли браузера:
 * 1. Скопируйте и вставьте этот код
 * 2. Вызовите нужную функцию
 */

// ============================================================
// 1. Базовая диагностика - показывает формат данных
// ============================================================
async function diagnoseApartments(perPage = 20) {
    console.log('='.repeat(80));
    console.log('🔍 ДИАГНОСТИКА КВАРТИР - ФОРМАТ ДАННЫХ');
    console.log('='.repeat(80));
    
    const response = await fetch(`/api/apartments/?per_page=${perPage}&sort=price_asc`);
    const data = await response.json();
    
    console.log(`\n📊 Всего квартир: ${data.total_count}`);
    console.log(`📊 На странице: ${data.apartments?.length || 0}`);
    
    if (!data.apartments?.length) {
        console.log('❌ Нет данных');
        return;
    }
    
    console.log('\n' + '-'.repeat(80));
    console.log('АНАЛИЗ ПОЛЕЙ ЦЕНЫ:');
    console.log('-'.repeat(80));
    
    let withPrice = 0;
    let withoutPrice = 0;
    let priceValues = [];
    
    data.apartments.forEach((apt, i) => {
        const hasPrice = apt.price && apt.price.toString().trim() !== '';
        const hasPriceNum = apt.price_num !== null && apt.price_num !== undefined;
        
        if (hasPrice || hasPriceNum) {
            withPrice++;
            if (hasPriceNum) priceValues.push(apt.price_num);
        } else {
            withoutPrice++;
        }
        
        if (i < 10) {
            console.log(`\n${i + 1}. ${apt.apartment_title || apt.title || 'Квартира'}`);
            console.log(`   ЖК: ${apt.complex_name || 'N/A'}`);
            console.log(`   price: "${apt.price}" (${typeof apt.price})`);
            console.log(`   price_num: ${apt.price_num} (${typeof apt.price_num})`);
            console.log(`   price_display: "${apt.price_display || 'N/A'}"`);
        }
    });
    
    console.log('\n' + '-'.repeat(80));
    console.log('СТАТИСТИКА:');
    console.log('-'.repeat(80));
    console.log(`   С ценой: ${withPrice}`);
    console.log(`   Без цены: ${withoutPrice}`);
    
    if (priceValues.length > 0) {
        console.log(`\n   Значения price_num (первые 10): ${priceValues.slice(0, 10).map(p => p?.toFixed(3)).join(', ')}`);
        console.log(`   Мин: ${Math.min(...priceValues.filter(p => p)).toFixed(3)} млн`);
        console.log(`   Макс: ${Math.max(...priceValues.filter(p => p)).toFixed(3)} млн`);
    }
    
    return data;
}

// ============================================================
// 2. Тест фильтра по цене
// ============================================================
async function testPriceFilter(priceTo, perPage = 30) {
    console.log('='.repeat(80));
    console.log(`🧪 ТЕСТ ФИЛЬТРА: до ${priceTo.toLocaleString('ru-RU')} ₽`);
    console.log('='.repeat(80));
    
    // Конвертируем в миллионы (как на бэкенде)
    const priceToMillions = priceTo >= 100 ? priceTo / 1000000 : priceTo;
    console.log(`\n📐 Конвертация: ${priceTo} → ${priceToMillions} млн`);
    
    const url = `/api/apartments/?per_page=${perPage}&sort=price_asc&price_to=${priceTo}`;
    console.log(`📡 Запрос: ${url}`);
    
    const response = await fetch(url);
    const data = await response.json();
    
    console.log(`\n✅ Ответ: ${data.total_count} квартир найдено`);
    
    if (!data.apartments?.length) {
        console.log('❌ Нет данных');
        return;
    }
    
    // Анализируем результаты
    let correct = 0;
    let incorrect = 0;
    let noPrice = 0;
    
    console.log('\n' + '-'.repeat(80));
    console.log('ПРОВЕРКА РЕЗУЛЬТАТОВ:');
    console.log('-'.repeat(80));
    
    data.apartments.forEach((apt, i) => {
        const priceNum = apt.price_num;
        const priceStr = apt.price || '';
        
        let status = '';
        if (priceNum === null || priceNum === undefined) {
            noPrice++;
            status = '❌ БЕЗ ЦЕНЫ (не должна быть в результатах!)';
        } else if (priceNum <= priceToMillions) {
            correct++;
            status = '✅ OK';
        } else {
            incorrect++;
            status = `❌ НЕВЕРНО: ${priceNum.toFixed(3)} > ${priceToMillions} млн`;
        }
        
        if (i < 15 || status.includes('❌')) {
            console.log(`${i + 1}. price_num=${priceNum?.toFixed(3) || 'null'}, price="${priceStr}" - ${status}`);
        }
    });
    
    console.log('\n' + '-'.repeat(80));
    console.log('ИТОГ:');
    console.log('-'.repeat(80));
    console.log(`   ✅ Корректных: ${correct}`);
    console.log(`   ❌ Некорректных: ${incorrect}`);
    console.log(`   ⚠️  Без цены: ${noPrice}`);
    
    if (incorrect > 0 || noPrice > 0) {
        console.log('\n🚨 ПРОБЛЕМА: фильтр работает неправильно!');
    } else {
        console.log('\n✅ Фильтр работает корректно');
    }
    
    return { data, correct, incorrect, noPrice };
}

// ============================================================
// 3. Проверка парсинга цены
// ============================================================
function testPriceParsing(priceString) {
    console.log('='.repeat(60));
    console.log(`🔧 ТЕСТ ПАРСИНГА: "${priceString}"`);
    console.log('='.repeat(60));
    
    // Симулируем логику бэкенда
    const digitsOnly = priceString.replace(/\D/g, '');
    console.log(`   Только цифры: "${digitsOnly}"`);
    
    if (digitsOnly) {
        const priceNum = parseFloat(digitsOnly) / 1000000;
        console.log(`   price_num: ${priceNum} млн`);
        console.log(`   Это: ${(priceNum * 1000000).toLocaleString('ru-RU')} ₽`);
        return priceNum;
    } else {
        console.log(`   ❌ Не удалось извлечь цену`);
        return null;
    }
}

// ============================================================
// 4. Проверка конвертации фильтра
// ============================================================
function testFilterConversion(filterValue) {
    console.log('='.repeat(60));
    console.log(`🔧 ТЕСТ КОНВЕРТАЦИИ ФИЛЬТРА: "${filterValue}"`);
    console.log('='.repeat(60));
    
    // Симулируем логику бэкенда convert_price_to_millions
    const priceClean = filterValue.toString().replace(/ /g, '').replace(',', '.');
    const priceVal = parseFloat(priceClean);
    
    console.log(`   Очищенное значение: "${priceClean}"`);
    console.log(`   Число: ${priceVal}`);
    
    let result;
    if (priceVal >= 100) {
        result = priceVal / 1000000;
        console.log(`   ${priceVal} >= 100 → конвертируем в миллионы: ${result}`);
    } else {
        result = priceVal;
        console.log(`   ${priceVal} < 100 → уже в миллионах: ${result}`);
    }
    
    return result;
}

// ============================================================
// 5. Полная диагностика
// ============================================================
async function fullDiagnosis() {
    console.log('\n\n');
    console.log('█'.repeat(80));
    console.log('█  ПОЛНАЯ ДИАГНОСТИКА ФИЛЬТРАЦИИ КВАРТИР ПО ЦЕНЕ');
    console.log('█'.repeat(80));
    
    // 1. Базовая диагностика
    await diagnoseApartments(15);
    
    console.log('\n\n');
    
    // 2. Тест парсинга разных форматов
    console.log('='.repeat(80));
    console.log('ТЕСТЫ ПАРСИНГА ЦЕН:');
    console.log('='.repeat(80));
    testPriceParsing('3 905 000 ₽');
    testPriceParsing('2 986 600 ₽');
    testPriceParsing('15000000');
    testPriceParsing('');
    
    console.log('\n\n');
    
    // 3. Тест конвертации фильтров
    console.log('='.repeat(80));
    console.log('ТЕСТЫ КОНВЕРТАЦИИ ФИЛЬТРА:');
    console.log('='.repeat(80));
    testFilterConversion('2000000');
    testFilterConversion('2 000 000');
    testFilterConversion('3.5');
    testFilterConversion('3,5');
    
    console.log('\n\n');
    
    // 4. Тесты фильтрации
    console.log('='.repeat(80));
    console.log('ТЕСТЫ ФИЛЬТРАЦИИ:');
    console.log('='.repeat(80));
    
    await testPriceFilter(2000000, 20);
    
    console.log('\n\n');
    await testPriceFilter(3000000, 20);
    
    console.log('\n\n');
    await testPriceFilter(5000000, 20);
}

// Экспорт функций
if (typeof window !== 'undefined') {
    window.diagnoseApartments = diagnoseApartments;
    window.testPriceFilter = testPriceFilter;
    window.testPriceParsing = testPriceParsing;
    window.testFilterConversion = testFilterConversion;
    window.fullDiagnosis = fullDiagnosis;
    
    console.log('✅ Функции загружены:');
    console.log('   diagnoseApartments(perPage)     - базовая диагностика');
    console.log('   testPriceFilter(priceTo)        - тест фильтра');
    console.log('   testPriceParsing(priceString)   - тест парсинга');
    console.log('   testFilterConversion(value)     - тест конвертации');
    console.log('   fullDiagnosis()                 - полная диагностика');
}

