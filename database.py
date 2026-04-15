"""
База данных - модели и инициализация
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import select, update
from config import config

Base = declarative_base()
engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    
    # Астрологические данные
    birth_date = Column(Date, nullable=True)
    birth_time = Column(String(10), nullable=True)      # "14:30"
    birth_city = Column(String(100), nullable=True)
    zodiac_sign = Column(String(20), nullable=True)
    
    # Подписка
    subscription_type = Column(String(20), default="free")  # free / base / premium
    subscription_expires = Column(DateTime, nullable=True)
    spreads_used_this_month = Column(Integer, default=0)
    spreads_month = Column(Integer, default=0)           # месяц последнего сброса
    total_spreads_free = Column(Integer, default=0)      # всего бесплатных использовано
    
    # Мета
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    language = Column(String(5), default="ru")
    referred_by = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)


class SpreadHistory(Base):
    __tablename__ = "spread_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    spread_type = Column(String(50))      # tarot_love / tarot_career / horoscope / compatibility
    question = Column(Text, nullable=True)
    result_text = Column(Text)
    cards_drawn = Column(String(200), nullable=True)   # JSON список карт
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    payment_id = Column(String(200), unique=True)      # ID от YooKassa или TG
    payment_type = Column(String(50))                   # single / base_sub / premium_sub
    amount = Column(Float)
    currency = Column(String(10), default="RUB")
    status = Column(String(20), default="pending")      # pending / success / failed
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


# ---- Хелперы ----

async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None) -> User:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Обновим last_active
            user.last_active = datetime.utcnow()
            await session.commit()
        return user


async def update_user(telegram_id: int, **kwargs):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(**kwargs)
        )
        await session.commit()


async def can_use_spread(telegram_id: int) -> tuple[bool, str]:
    """
    Проверяет может ли пользователь использовать расклад.
    Возвращает (True/False, причина_отказа)
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return False, "user_not_found"

        now = datetime.utcnow()

        # Премиум — безлимит
        if user.subscription_type == "premium":
            if user.subscription_expires and user.subscription_expires > now:
                return True, "premium"

        # Базовая подписка — 5/мес
        if user.subscription_type == "base":
            if user.subscription_expires and user.subscription_expires > now:
                current_month = now.month
                if user.spreads_month != current_month:
                    # Новый месяц — сбросить счётчик
                    await session.execute(
                        update(User).where(User.telegram_id == telegram_id).values(
                            spreads_used_this_month=0,
                            spreads_month=current_month
                        )
                    )
                    await session.commit()
                    return True, "base"
                if user.spreads_used_this_month < config.BASE_SPREADS_PER_MONTH:
                    return True, "base"
                else:
                    return False, "base_limit"

        # Бесплатный — 1 раз
        if user.total_spreads_free < config.FREE_SPREADS_TOTAL:
            return True, "free"

        return False, "no_subscription"


async def increment_spread_count(telegram_id: int, spread_type: str, question: str, result: str, cards: str = None, is_paid: bool = False):
    async with AsyncSessionLocal() as session:
        # Инкремент счётчика
        result_q = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result_q.scalar_one_or_none()
        if user:
            now = datetime.utcnow()
            current_month = now.month
            
            if user.subscription_type == "free" or not user.subscription_type:
                user.total_spreads_free += 1
            elif user.subscription_type == "base":
                if user.spreads_month != current_month:
                    user.spreads_used_this_month = 1
                    user.spreads_month = current_month
                else:
                    user.spreads_used_this_month += 1

            # Сохраняем историю
            history = SpreadHistory(
                user_id=telegram_id,
                spread_type=spread_type,
                question=question,
                result_text=result,
                cards_drawn=cards,
                is_paid=is_paid
            )
            session.add(history)
            await session.commit()
