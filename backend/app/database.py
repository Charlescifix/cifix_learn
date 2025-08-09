"""
Database configuration and session management
Simple async SQLAlchemy setup for CIFIX LEARN
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async database engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.APP_DEBUG,
    pool_size=5,  # Small pool for 10-15 users
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800  # 30 minutes
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_database():
    """Initialize database with tables and data"""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Test connection
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            
        logger.info("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def check_database_health() -> bool:
    """Check if database is healthy"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Simple connection test
async def test_connection():
    """Test database connection on startup"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise e