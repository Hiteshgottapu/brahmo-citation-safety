import asyncio
from backend.database import get_supabase
async def fix_db():
    try:
        supabase = await get_supabase()
        res = await supabase.table('section_mappings').update({'new_section': '101'}).eq('old_section', '302').execute()
        print('Updated rows:', res.data)
    except Exception as e:
        print('Error:', e)
asyncio.run(fix_db())
