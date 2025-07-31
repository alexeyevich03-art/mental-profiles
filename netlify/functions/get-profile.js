const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event) => {
  // Отримуємо ID профілю з параметрів запиту
  const { id } = event.queryStringParameters;
  
  // Перевіряємо, чи ID не пустий
  if (!id || typeof id !== 'string') {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Не вказано ID профілю або невірний формат' }),
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    };
  }

  // Ініціалізуємо клієнт Supabase з додатковими налаштуваннями
  const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_KEY,
    {
      db: {
        schema: 'public'
      },
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    }
  );
  
  try {
    // Виконуємо запит до Supabase
    const { data, error } = await supabase
      .from('profiles')
      .select('profile_content')
      .eq('id', id)  // ID тепер TEXT типу
      .single();

    if (error) throw error;
    
    // Якщо профіль не знайдено
    if (!data) {
      return {
        statusCode: 404,
        body: '<h1>Профіль не знайдено</h1><p>Вказаний профіль не існує або був видалений</p>',
        headers: { 
          'Content-Type': 'text/html',
          'Access-Control-Allow-Origin': '*'
        }
      };
    }
    
    // Успішна відповідь
    return {
      statusCode: 200,
      headers: { 
        'Content-Type': 'text/html',
        'Access-Control-Allow-Origin': '*'
      },
      body: data.profile_content
    };
    
  } catch (error) {
    // Обробка помилок
    console.error('Помилка при отриманні профілю:', error);
    
    return {
      statusCode: 500,
      body: `<h1>Помилка сервера</h1><p>Не вдалося завантажити профіль. Будь ласка, спробуйте пізніше.</p>`,
      headers: { 
        'Content-Type': 'text/html',
        'Access-Control-Allow-Origin': '*'
      }
    };
  }
};
