import aiosqlite

t = 'bikes'

async def get_all_bikes():
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT * FROM {t}
        """)
        bikes = await cursor.fetchall()

        return bikes

async def get_bike_by_type(bike):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT * FROM {t} WHERE bike_type = ? AND is_free = True
        """, (bike, ))
        bikes = await cursor.fetchall()

        return bikes

async def get_bike_by_id(bike_id):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT * FROM {t} WHERE id = ?
        """, (bike_id, ))

        result = await cursor.fetchone()

        return result

async def change_status_not_free(bike_id, tg_id):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        UPDATE {t} 
        SET is_free = False, user = ? 
        WHERE bike_id = ? 
        """, (tg_id, bike_id))

        await conn.commit()


