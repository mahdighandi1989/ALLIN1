from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for common database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results"""
        try:
            result = await self.session.execute(text(query), params or {})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    async def execute_scalar(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a query and return a single scalar value"""
        try:
            result = await self.session.execute(text(query), params or {})
            return result.scalar()
        except Exception as e:
            logger.error(f"Database scalar query error: {e}")
            raise
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = :table_name
        );
        """
        result = await self.execute_scalar(query, {"table_name": table_name})
        return bool(result)
    
    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position;
        """
        return await self.execute_query(query, {"table_name": table_name})
    
    async def backup_table(self, table_name: str, backup_suffix: str = "backup") -> str:
        """Create a backup of a table"""
        backup_table_name = f"{table_name}_{backup_suffix}"
        query = f"CREATE TABLE {backup_table_name} AS SELECT * FROM {table_name};"
        await self.session.execute(text(query))
        await self.session.commit()
        return backup_table_name