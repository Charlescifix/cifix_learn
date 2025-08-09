"""
Database initialization script for CIFIX LEARN
Creates tables and populates with initial data
"""
import asyncio
import logging
from sqlalchemy import text
from datetime import datetime
import uuid

from app.database import engine, AsyncSessionLocal
from app.models.user import Base as UserBase
from app.models.analytics import Base as AnalyticsBase
from app.core.security import get_password_hash
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(AnalyticsBase.metadata.create_all)
    
    logger.info("✅ Database tables created successfully")

async def create_initial_data():
    """Create initial data for the application"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Creating initial data...")
            
            # Create learning paths
            learning_paths_sql = """
            INSERT INTO learning_paths (id, name, slug, description, icon, difficulty_level, estimated_hours, sort_order, is_active, created_at)
            VALUES 
                (:game_id, 'Game Development', 'game-development', 'Learn to create games using Python, Scratch, and Unity. Build interactive experiences and learn programming through play.', '🎮', 'beginner', 40, 1, true, :now),
                (:ai_id, 'AI & Machine Learning', 'ai-machine-learning', 'Discover artificial intelligence and machine learning concepts. Create smart programs and understand how computers learn.', '🤖', 'intermediate', 50, 2, true, :now),
                (:web_id, 'Web Development', 'web-development', 'Build websites and web applications using HTML, CSS, JavaScript, and modern frameworks.', '🌐', 'beginner', 45, 3, true, :now),
                (:robotics_id, 'Robotics', 'robotics', 'Program robots and learn about hardware integration. Combine coding with physical computing.', '🤖', 'intermediate', 60, 4, true, :now),
                (:data_id, 'Data Science', 'data-science', 'Analyze data, create visualizations, and discover insights using Python and data tools.', '📊', 'advanced', 55, 5, true, :now),
                (:mobile_id, 'Mobile App Development', 'mobile-app-development', 'Create mobile applications for iOS and Android using modern development frameworks.', '📱', 'intermediate', 50, 6, true, :now),
                (:general_id, 'General Programming', 'general-programming', 'Learn fundamental programming concepts using Python. Perfect for beginners starting their coding journey.', '💻', 'beginner', 35, 7, true, :now)
            ON CONFLICT (slug) DO NOTHING;
            """
            
            # Generate UUIDs for paths
            path_ids = {
                'game_id': str(uuid.uuid4()),
                'ai_id': str(uuid.uuid4()),
                'web_id': str(uuid.uuid4()),
                'robotics_id': str(uuid.uuid4()),
                'data_id': str(uuid.uuid4()),
                'mobile_id': str(uuid.uuid4()),
                'general_id': str(uuid.uuid4()),
                'now': datetime.utcnow()
            }
            
            await db.execute(text(learning_paths_sql), path_ids)
            
            # Create learning modules for each path
            modules_data = []
            
            # Game Development modules
            game_modules = [
                ("Introduction to Game Development", "Learn the basics of game development, game engines, and design principles.", 1),
                ("Scratch Programming", "Create your first games using Scratch visual programming language.", 2),
                ("Python Game Development", "Build games using Python and Pygame library.", 3),
                ("Game Design Principles", "Learn about game mechanics, level design, and player experience.", 4),
                ("2D Graphics and Animation", "Create sprites, animations, and visual effects for games.", 5),
                ("Game Project Workshop", "Build a complete game project from concept to completion.", 6)
            ]
            
            for title, description, sort_order in game_modules:
                modules_data.append({
                    'id': str(uuid.uuid4()),
                    'path_id': path_ids['game_id'],
                    'title': title,
                    'description': description,
                    'difficulty_level': 'beginner',
                    'estimated_hours': 6,
                    'sort_order': sort_order,
                    'is_locked': sort_order > 1,
                    'learning_objectives': [
                        f"Understand {title.lower()} concepts",
                        "Apply learned skills in practical exercises",
                        "Complete hands-on projects"
                    ],
                    'topics': [title.lower().replace(' ', '_')],
                    'is_active': True,
                    'created_at': datetime.utcnow()
                })
            
            # AI & Machine Learning modules
            ai_modules = [
                ("Introduction to AI", "Understand artificial intelligence concepts and applications.", 1),
                ("Python for AI", "Learn Python programming specifically for AI development.", 2),
                ("Machine Learning Basics", "Explore supervised and unsupervised learning algorithms.", 3),
                ("Neural Networks", "Build and train neural networks from scratch.", 4),
                ("Computer Vision", "Process images and videos using AI techniques.", 5),
                ("AI Project Development", "Create a complete AI application project.", 6)
            ]
            
            for title, description, sort_order in ai_modules:
                modules_data.append({
                    'id': str(uuid.uuid4()),
                    'path_id': path_ids['ai_id'],
                    'title': title,
                    'description': description,
                    'difficulty_level': 'intermediate',
                    'estimated_hours': 8,
                    'sort_order': sort_order,
                    'is_locked': sort_order > 1,
                    'learning_objectives': [
                        f"Master {title.lower()} fundamentals",
                        "Implement practical AI solutions",
                        "Understand ethical AI principles"
                    ],
                    'topics': [title.lower().replace(' ', '_')],
                    'is_active': True,
                    'created_at': datetime.utcnow()
                })
            
            # Web Development modules
            web_modules = [
                ("HTML & CSS Fundamentals", "Learn the building blocks of web pages.", 1),
                ("JavaScript Basics", "Add interactivity to web pages with JavaScript.", 2),
                ("Responsive Web Design", "Create websites that work on all devices.", 3),
                ("Web Development Frameworks", "Explore modern frameworks like React or Vue.", 4),
                ("Backend Development", "Learn server-side programming and databases.", 5),
                ("Full-Stack Project", "Build a complete web application from front to back.", 6)
            ]
            
            for title, description, sort_order in web_modules:
                modules_data.append({
                    'id': str(uuid.uuid4()),
                    'path_id': path_ids['web_id'],
                    'title': title,
                    'description': description,
                    'difficulty_level': 'beginner',
                    'estimated_hours': 7,
                    'sort_order': sort_order,
                    'is_locked': sort_order > 1,
                    'learning_objectives': [
                        f"Build proficiency in {title.lower()}",
                        "Create responsive web interfaces",
                        "Deploy web applications"
                    ],
                    'topics': [title.lower().replace(' & ', '_').replace(' ', '_')],
                    'is_active': True,
                    'created_at': datetime.utcnow()
                })
            
            # Insert all modules
            for module_data in modules_data:
                module_sql = """
                INSERT INTO learning_modules 
                (id, path_id, title, description, difficulty_level, estimated_hours, sort_order, is_locked, learning_objectives, topics, is_active, created_at)
                VALUES 
                (:id, :path_id, :title, :description, :difficulty_level, :estimated_hours, :sort_order, :is_locked, :learning_objectives, :topics, :is_active, :created_at)
                ON CONFLICT (id) DO NOTHING;
                """
                await db.execute(text(module_sql), module_data)
            
            # Create achievement types
            achievements_sql = """
            INSERT INTO achievement_types (id, name, description, icon, points, is_active, created_at)
            VALUES 
                (:first_id, 'First Steps', 'Complete your first learning module', '🎯', 10, true, :now),
                (:quick_id, 'Quick Learner', 'Complete 3 modules in one day', '⚡', 25, true, :now),
                (:path_id, 'Path Completer', 'Complete an entire learning path', '🏆', 100, true, :now),
                (:perfect_id, 'Perfect Score', 'Score 100% on an assessment', '💯', 50, true, :now),
                (:streak_id, 'Learning Streak', 'Learn for 7 consecutive days', '🔥', 75, true, :now)
            ON CONFLICT (name) DO NOTHING;
            """
            
            achievement_ids = {
                'first_id': str(uuid.uuid4()),
                'quick_id': str(uuid.uuid4()),
                'path_id': str(uuid.uuid4()),
                'perfect_id': str(uuid.uuid4()),
                'streak_id': str(uuid.uuid4()),
                'now': datetime.utcnow()
            }
            
            await db.execute(text(achievements_sql), achievement_ids)
            
            # Create sample admin user for testing (optional)
            try:
                admin_sql = """
                INSERT INTO users (id, email, password_hash, first_name, last_name, email_verified, is_active, created_at)
                VALUES (:id, :email, :password_hash, :first_name, :last_name, true, true, :now)
                ON CONFLICT (email) DO NOTHING;
                """
                
                admin_data = {
                    'id': str(uuid.uuid4()),
                    'email': 'admin@cifixlearn.com',
                    'password_hash': get_password_hash('CifixAdmin2024!'),
                    'first_name': 'CIFIX',
                    'last_name': 'Administrator',
                    'now': datetime.utcnow()
                }
                
                await db.execute(text(admin_sql), admin_data)
                logger.info("✅ Sample admin user created for testing")
            except Exception as e:
                logger.warning(f"Admin user creation failed (may already exist): {e}")
            
            await db.commit()
            logger.info("✅ Initial data created successfully")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to create initial data: {e}")
            raise e

async def check_database_connection():
    """Check if database connection is working"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def main():
    """Main initialization function"""
    logger.info("🚀 Starting CIFIX LEARN database initialization...")
    
    # Check database connection
    if not await check_database_connection():
        logger.error("❌ Cannot connect to database. Check your DATABASE_URL configuration.")
        return
    
    try:
        # Create tables
        await create_tables()
        
        # Create initial data
        await create_initial_data()
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info("📚 Learning paths created: Game Development, AI & ML, Web Development, and more")
        logger.info("🏆 Achievement system initialized")
        logger.info("👤 Admin user ready (if configured)")
        logger.info("")
        logger.info("🎯 Next steps:")
        logger.info("   1. Start the FastAPI server: uvicorn app.main:app --reload")
        logger.info("   2. Access the API docs at: http://localhost:8000/docs")
        logger.info("   3. Test the endpoints and create your first user")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise e
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())