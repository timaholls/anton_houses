// ============================================
// Диагностика фильтрации по этажам
// Вставьте этот код в консоль браузера на странице детальной ЖК
// ============================================

(async function() {
    console.log('🔍 ДИАГНОСТИКА ФИЛЬТРАЦИИ ПО ЭТАЖАМ');
    console.log('================================================================================');
    
    // Получаем ID ЖК из URL
    const urlParts = window.location.pathname.split('/');
    let complexId = null;
    for (let i = 0; i < urlParts.length; i++) {
        if (urlParts[i] === 'complex' && urlParts[i + 1]) {
            complexId = urlParts[i + 1];
            break;
        }
    }
    
    if (!complexId) {
        console.error('❌ Не удалось определить ID ЖК из URL');
        console.log('Текущий URL:', window.location.pathname);
        return;
    }
    
    console.log('📍 ID ЖК:', complexId);
    console.log('');
    
    // Шаг 1: Загружаем ВСЕ квартиры без фильтров
    console.log('📡 ШАГ 1: Загрузка всех квартир без фильтров');
    console.log('--------------------------------------------------------------------------------');
    
    let allApartments = [];
    const types = ['Студия', '1', '2', '3', '4', '5+'];
    
    for (const type of types) {
        try {
            // Загружаем первую страницу для получения total_count
            const url = `/api/complex/${complexId}/apartments/?type=${encodeURIComponent(type)}&per_page=100`;
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.total_count > 0) {
                console.log(`   ✅ Тип "${type}": ${data.total_count} квартир`);
                
                // Загружаем все страницы
                let page = 1;
                let loaded = 0;
                
                while (loaded < data.total_count) {
                    const pageUrl = `/api/complex/${complexId}/apartments/?type=${encodeURIComponent(type)}&per_page=100&page=${page}`;
                    const pageResponse = await fetch(pageUrl);
                    const pageData = await pageResponse.json();
                    
                    if (pageData.apartments && pageData.apartments.length > 0) {
                        allApartments.push(...pageData.apartments.map(apt => ({...apt, type})));
                        loaded += pageData.apartments.length;
                        page++;
                    } else {
                        break;
                    }
                }
                
                console.log(`      Загружено: ${loaded} из ${data.total_count}`);
            }
        } catch (e) {
            console.log(`   ⚠️ Тип "${type}": ошибка - ${e.message}`);
        }
    }
    
    console.log(`\n📊 Всего квартир загружено: ${allApartments.length}`);
    console.log('');
    
    // Шаг 2: Анализ этажей
    console.log('📡 ШАГ 2: Анализ этажей квартир');
    console.log('--------------------------------------------------------------------------------');
    
    const floorStats = {
        withFloorMin: 0,
        withFloorMax: 0,
        withBoth: 0,
        withoutFloor: 0,
        floorRanges: []
    };
    
    allApartments.forEach(apt => {
        const floorMin = apt.floor_min;
        const floorMax = apt.floor_max;
        const floor = apt.floor || '';
        
        if (floorMin !== null && floorMin !== undefined) {
            floorStats.withFloorMin++;
        }
        if (floorMax !== null && floorMax !== undefined) {
            floorStats.withFloorMax++;
        }
        if (floorMin !== null && floorMax !== null) {
            floorStats.withBoth++;
            floorStats.floorRanges.push({
                type: apt.type,
                floorMin,
                floorMax,
                floor,
                title: apt.title
            });
        } else {
            floorStats.withoutFloor++;
        }
    });
    
    console.log(`   С floorMin: ${floorStats.withFloorMin}`);
    console.log(`   С floorMax: ${floorStats.withFloorMax}`);
    console.log(`   С обоими (floorMin и floorMax): ${floorStats.withBoth}`);
    console.log(`   Без этажей: ${floorStats.withoutFloor}`);
    console.log('');
    
    if (floorStats.floorRanges.length > 0) {
        console.log('   📋 Примеры диапазонов этажей:');
        floorStats.floorRanges.slice(0, 10).forEach((item, i) => {
            console.log(`   ${i + 1}. ${item.type}: ${item.floorMin}-${item.floorMax} (floor="${item.floor}")`);
        });
        if (floorStats.floorRanges.length > 10) {
            console.log(`   ... и ещё ${floorStats.floorRanges.length - 10}`);
        }
    }
    console.log('');
    
    // Шаг 3: Тест фильтра "от 5"
    console.log('📡 ШАГ 3: Тест фильтра "от 5" (floor_from=5)');
    console.log('--------------------------------------------------------------------------------');
    
    try {
        const url3 = `/api/complex/${complexId}/apartments/?floor_from=5`;
        const response3 = await fetch(url3);
        const data3 = await response3.json();
        
        console.log(`   ✅ API вернул: ${data3.total_count} квартир`);
        
        // Проверяем логику вручную
        const expectedCount = floorStats.floorRanges.filter(item => item.floorMin >= 5).length;
        console.log(`   📊 Ожидается (floorMin >= 5): ${expectedCount} квартир`);
        
        if (data3.apartments && data3.apartments.length > 0) {
            console.log('');
            console.log('   📋 Первые 5 квартир из ответа:');
            data3.apartments.slice(0, 5).forEach((apt, i) => {
                console.log(`   ${i + 1}. type=${apt.type}, floor_min=${apt.floor_min}, floor_max=${apt.floor_max}, floor="${apt.floor}"`);
            });
            
            // Проверяем, что все квартиры действительно проходят фильтр
            const invalid = data3.apartments.filter(apt => {
                if (apt.floor_min === null || apt.floor_min === undefined) return true;
                return apt.floor_min < 5;
            });
            
            if (invalid.length > 0) {
                console.error(`   ❌ ОШИБКА: ${invalid.length} квартир не должны проходить фильтр!`);
                invalid.forEach(apt => {
                    console.error(`      - type=${apt.type}, floor_min=${apt.floor_min}`);
                });
            } else {
                console.log('   ✅ Все квартиры корректно прошли фильтр');
            }
        }
    } catch (e) {
        console.error('   ❌ Ошибка:', e.message);
    }
    
    console.log('');
    
    // Шаг 4: Тест фильтра "до 10"
    console.log('📡 ШАГ 4: Тест фильтра "до 10" (floor_to=10)');
    console.log('--------------------------------------------------------------------------------');
    
    try {
        const url4 = `/api/complex/${complexId}/apartments/?floor_to=10`;
        const response4 = await fetch(url4);
        const data4 = await response4.json();
        
        console.log(`   ✅ API вернул: ${data4.total_count} квартир`);
        
        // Проверяем логику вручную
        const expectedCount4 = floorStats.floorRanges.filter(item => item.floorMax <= 10).length;
        console.log(`   📊 Ожидается (floorMax <= 10): ${expectedCount4} квартир`);
        
        if (data4.apartments && data4.apartments.length > 0) {
            console.log('');
            console.log('   📋 Первые 5 квартир из ответа:');
            data4.apartments.slice(0, 5).forEach((apt, i) => {
                console.log(`   ${i + 1}. type=${apt.type}, floor_min=${apt.floor_min}, floor_max=${apt.floor_max}, floor="${apt.floor}"`);
            });
            
            // Проверяем, что все квартиры действительно проходят фильтр
            const invalid4 = data4.apartments.filter(apt => {
                if (apt.floor_max === null || apt.floor_max === undefined) return true;
                return apt.floor_max > 10;
            });
            
            if (invalid4.length > 0) {
                console.error(`   ❌ ОШИБКА: ${invalid4.length} квартир не должны проходить фильтр!`);
                invalid4.forEach(apt => {
                    console.error(`      - type=${apt.type}, floor_max=${apt.floor_max}`);
                });
            } else {
                console.log('   ✅ Все квартиры корректно прошли фильтр');
            }
        }
    } catch (e) {
        console.error('   ❌ Ошибка:', e.message);
    }
    
    console.log('');
    
    // Шаг 5: Тест фильтра "от 5 до 10"
    console.log('📡 ШАГ 5: Тест фильтра "от 5 до 10" (floor_from=5&floor_to=10)');
    console.log('--------------------------------------------------------------------------------');
    
    try {
        const url5 = `/api/complex/${complexId}/apartments/?floor_from=5&floor_to=10`;
        const response5 = await fetch(url5);
        const data5 = await response5.json();
        
        console.log(`   ✅ API вернул: ${data5.total_count} квартир`);
        
        // Проверяем логику вручную
        const expectedCount5 = floorStats.floorRanges.filter(item => 
            item.floorMin >= 5 && item.floorMax <= 10
        ).length;
        console.log(`   📊 Ожидается (floorMin >= 5 AND floorMax <= 10): ${expectedCount5} квартир`);
        
        if (data5.apartments && data5.apartments.length > 0) {
            console.log('');
            console.log('   📋 Первые 5 квартир из ответа:');
            data5.apartments.slice(0, 5).forEach((apt, i) => {
                console.log(`   ${i + 1}. type=${apt.type}, floor_min=${apt.floor_min}, floor_max=${apt.floor_max}, floor="${apt.floor}"`);
            });
            
            // Проверяем, что все квартиры действительно проходят фильтр
            const invalid5 = data5.apartments.filter(apt => {
                if (apt.floor_min === null || apt.floor_max === null) return true;
                return apt.floor_min < 5 || apt.floor_max > 10;
            });
            
            if (invalid5.length > 0) {
                console.error(`   ❌ ОШИБКА: ${invalid5.length} квартир не должны проходить фильтр!`);
                invalid5.forEach(apt => {
                    console.error(`      - type=${apt.type}, floor_min=${apt.floor_min}, floor_max=${apt.floor_max}`);
                });
            } else {
                console.log('   ✅ Все квартиры корректно прошли фильтр');
            }
        }
    } catch (e) {
        console.error('   ❌ Ошибка:', e.message);
    }
    
    console.log('');
    
    // Шаг 6: Тест с типом квартир
    console.log('📡 ШАГ 6: Тест фильтра "от 5" для типа "Студия"');
    console.log('--------------------------------------------------------------------------------');
    
    try {
        const url6 = `/api/complex/${complexId}/apartments/?type=Студия&floor_from=5`;
        const response6 = await fetch(url6);
        const data6 = await response6.json();
        
        console.log(`   ✅ API вернул: ${data6.total_count} студий с этажом >= 5`);
        
        if (data6.apartments && data6.apartments.length > 0) {
            console.log('');
            console.log('   📋 Все студии из ответа:');
            data6.apartments.forEach((apt, i) => {
                console.log(`   ${i + 1}. floor_min=${apt.floor_min}, floor_max=${apt.floor_max}, floor="${apt.floor}", title="${apt.title}"`);
            });
        }
    } catch (e) {
        console.error('   ❌ Ошибка:', e.message);
    }
    
    console.log('');
    console.log('================================================================================');
    console.log('🔍 ДИАГНОСТИКА ЗАВЕРШЕНА');
    console.log('');
    console.log('💡 Для ручного теста используйте:');
    console.log(`   fetch('/api/complex/${complexId}/apartments/?floor_from=5').then(r => r.json()).then(console.log)`);
})();

