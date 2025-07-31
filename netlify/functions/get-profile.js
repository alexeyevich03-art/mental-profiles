const { createClient } = require('@supabase/supabase-js')

exports.handler = async (event) => {
  // Перевірка наявності обов'язкових змінних
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Supabase credentials not configured' }),
      headers: { 'Content-Type': 'application/json' }
    }
  }

  // Отримання ID з параметрів запиту
  const { id } = event.queryStringParameters || {}
  if (!id) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Profile ID is required' }),
      headers: { 'Content-Type': 'application/json' }
    }
  }

  try {
    // Ініціалізація клієнта Supabase
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_KEY,
      {
        auth: { persistSession: false }
      }
    )

    // Запит до бази даних
    const { data, error } = await supabase
      .from('profiles')
      .select('profile_content')
      .eq('id', id)
      .single()

    if (error) throw error
    if (!data) throw new Error('Profile not found')

    // Успішна відповідь
    return {
      statusCode: 200,
      headers: { 
        'Content-Type': 'text/html',
        'Access-Control-Allow-Origin': '*'
      },
      body: data.profile_content
    }

  } catch (error) {
    // Обробка помилок
    console.error('Error:', error.message)
    return {
      statusCode: 500,
      body: JSON.stringify({ 
        error: 'Failed to fetch profile',
        details: error.message 
      }),
      headers: { 'Content-Type': 'application/json' }
    }
  }
}
