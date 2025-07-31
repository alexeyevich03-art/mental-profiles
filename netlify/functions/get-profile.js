const { createClient } = require('@supabase/supabase-js')

exports.handler = async (event) => {
  // Перевірка змінних оточення
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Не налаштовано підключення до бази даних' }),
      headers: { 'Content-Type': 'application/json' }
    }
  }

  const { id } = event.queryStringParameters || {}
  
  if (!id) {
    return {
      statusCode: 400,
      body: '<h1>Помилка</h1><p>Не вказано ID профілю</p>',
      headers: { 'Content-Type': 'text/html' }
    }
  }

  // Ініціалізація клієнта з явною перевіркою URL
  const supabaseUrl = process.env.SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_KEY
  
  if (!supabaseUrl || !supabaseKey) {
    console.error('Supabase credentials missing')
    return {
      statusCode: 500,
      body: '<h1>Помилка сервера</h1><p>Спробуйте пізніше</p>',
      headers: { 'Content-Type': 'text/html' }
    }
  }

  const supabase = createClient(supabaseUrl, supabaseKey, {
    auth: { persistSession: false }
  })

  try {
    const { data, error } = await supabase
      .from('profiles')
      .select('profile_content')
      .eq('id', id)
      .single()

    if (error) throw error
    
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/html' },
      body: data?.profile_content || '<h1>Профіль не знайдено</h1>'
    }
  } catch (error) {
    console.error('Database error:', error)
    return {
      statusCode: 500,
      body: `<h1>Помилка</h1><p>${error.message}</p>`,
      headers: { 'Content-Type': 'text/html' }
    }
  }
}
