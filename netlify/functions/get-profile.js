const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event) => {
  const { id } = event.queryStringParameters;
  const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_KEY);
  
  try {
    const { data, error } = await supabase
      .from('profiles')
      .select('profile_content')
      .eq('id', id)
      .single();

    if (error) throw error;
    
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/html' },
      body: data.profile_content
    };
    
  } catch (error) {
    return {
      statusCode: 500,
      body: `<h1>Помилка</h1><p>Не вдалося завантажити профіль: ${error.message}</p>`
    };
  }
};