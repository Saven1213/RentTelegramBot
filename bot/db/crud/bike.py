import aiosqlite



async def get_all_bikes():
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT * FROM bikes
        """)
        bikes = await cursor.fetchall()

        return bikes

async def get_bike_by_type(bike):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT * FROM bikes WHERE bike_type = ? AND is_free = True
        """, (bike, ))
        bikes = await cursor.fetchall()

        return bikes

async def get_bike_by_id(bike_id):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT * FROM bikes WHERE id = ?
        """, (bike_id, ))

        result = await cursor.fetchone()

        return result