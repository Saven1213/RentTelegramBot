from email.policy import default

from sqlalchemy import String, Integer, Boolean, Float, DateTime
from sqlalchemy.orm import Mapped
from typing import Optional
from aiogram.client.default import Default
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase,Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, async_session
from datetime import datetime

engine = create_async_engine(url='sqlite+aiosqlite:///rent-bike.db')

async_sess = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column()

    username: Mapped[str] = mapped_column()

    bike_id: Mapped[int] = mapped_column(nullable=True)
    bike_name: Mapped[str] = mapped_column(nullable=True)





    refferals: Mapped[int] = mapped_column(default=0)

    ban: Mapped[bool] = mapped_column(Boolean, default=False)

    admin: Mapped[str] = mapped_column(String, default='user')

class Bike(Base):
    __tablename__ = 'bikes'

    id: Mapped[int] = mapped_column(primary_key=True)

    bike_id: Mapped[int] = mapped_column()
    bike_type: Mapped[str] = mapped_column(String)

    user: Mapped[int] = mapped_column(nullable=True)

    change_oil_at: Mapped[int] = mapped_column()

    gas: Mapped[str] = mapped_column()

    is_free: Mapped[bool] = mapped_column(Boolean, default=True)




class Payment(Base):
    __tablename__ = "payments"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    order_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    bill_id: Mapped[Optional[str]] = mapped_column(String(50))

    # Финансовые данные
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    commission: Mapped[float] = mapped_column(Float, default=0.0)

    # Статусы
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")


    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)


    description: Mapped[Optional[str]] = mapped_column(String(300))


class RentDetail(Base):
    __tablename__ = 'rent_details'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    bike_id: Mapped[int] = mapped_column(ForeignKey('bikes.id'))
    nitified: Mapped[int] = mapped_column(Integer, default=0)
    start_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default='active')  # 'active'/'completed'/'cancelled'


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)







