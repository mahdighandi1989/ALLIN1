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
        try:
            result = await self.execute_scalar(query, {"table_name": table_name})
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking table existence for '{table_name}': {e}")
            return False
    
    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position;
        """
        try:
            return await self.execute_query(query, {"table_name": table_name})
        except Exception as e:
            logger.error(f"Error retrieving columns for table '{table_name}': {e}")
            return []
    
    async def backup_table(self, table_name: str, backup_suffix: str = "backup") -> Optional[str]:
        """
        Create a backup of a table
        
        Args:
            table_name: Name of the table to backup
            backup_suffix: Suffix for the backup table name
            
        Returns:
            Backup table name if successful, None if failed
            
        Raises:
            Exception: If backup operation fails
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")
        
        if not backup_suffix or not isinstance(backup_suffix, str):
            raise ValueError("Backup suffix must be a non-empty string")
        
        # Sanitize table names to prevent SQL injection
        sanitized_table_name = table_name.replace('"', '').replace("'", "").replace(";", "")
        sanitized_backup_suffix = backup_suffix.replace('"', '').replace("'", "").replace(";", "")
        
        backup_table_name = f"{sanitized_table_name}_{sanitized_backup_suffix}"
        
        try:
            # Check if source table exists
            if not await self.check_table_exists(sanitized_table_name):
                raise ValueError(f"Source table '{sanitized_table_name}' does not exist")
            
            # Check if backup table already exists
            if await self.check_table_exists(backup_table_name):
                logger.warning(f"Backup table '{backup_table_name}' already exists, dropping it")
                drop_query = f'DROP TABLE "{backup_table_name}"'
                await self.session.execute(text(drop_query))
            
            # Create backup table
            backup_query = f'CREATE TABLE "{backup_table_name}" AS SELECT * FROM "{sanitized_table_name}"'
            await self.session.execute(text(backup_query))
            
            # Verify backup was created successfully
            if not await self.check_table_exists(backup_table_name):
                raise Exception(f"Failed to create backup table '{backup_table_name}'")
            
            logger.info(f"Successfully created backup table '{backup_table_name}' from '{sanitized_table_name}'")
            return backup_table_name
            
        except Exception as e:
            logger.error(f"Failed to backup table '{sanitized_table_name}': {e}")
            # Rollback any partial changes
            await self.session.rollback()
            raise Exception(f"Backup operation failed: {e}")
    
    async def drop_table(self, table_name: str, if_exists: bool = True) -> bool:
        """
        Drop a table safely
        
        Args:
            table_name: Name of the table to drop
            if_exists: If True, don't raise error if table doesn't exist
            
        Returns:
            True if table was dropped, False if it didn't exist (when if_exists=True)
            
        Raises:
            Exception: If drop operation fails
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")
        
        # Sanitize table name
        sanitized_table_name = table_name.replace('"', '').replace("'", "").replace(";", "")
        
        try:
            # Check if table exists
            table_exists = await self.check_table_exists(sanitized_table_name)
            
            if not table_exists:
                if if_exists:
                    logger.info(f"Table '{sanitized_table_name}' does not exist, skipping drop")
                    return False
                else:
                    raise ValueError(f"Table '{sanitized_table_name}' does not exist")
            
            # Drop table
            drop_query = f'DROP TABLE "{sanitized_table_name}"'
            await self.session.execute(text(drop_query))
            
            logger.info(f"Successfully dropped table '{sanitized_table_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop table '{sanitized_table_name}': {e}")
            await self.session.rollback()
            raise Exception(f"Drop table operation failed: {e}")
    
    async def get_table_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of rows in the table
            
        Raises:
            Exception: If operation fails
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")
        
        # Sanitize table name
        sanitized_table_name = table_name.replace('"', '').replace("'", "").replace(";", "")
        
        try:
            # Check if table exists
            if not await self.check_table_exists(sanitized_table_name):
                raise ValueError(f"Table '{sanitized_table_name}' does not exist")
            
            # Get row count
            count_query = f'SELECT COUNT(*) FROM "{sanitized_table_name}"'
            result = await self.execute_scalar(count_query)
            
            return int(result) if result is not None else 0
            
        except Exception as e:
            logger.error(f"Failed to get row count for table '{sanitized_table_name}': {e}")
            raise Exception(f"Row count operation failed: {e}")
    
    async def truncate_table(self, table_name: str) -> bool:
        """
        Truncate a table (remove all rows)
        
        Args:
            table_name: Name of the table to truncate
            
        Returns:
            True if successful
            
        Raises:
            Exception: If operation fails
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")
        
        # Sanitize table name
        sanitized_table_name = table_name.replace('"', '').replace("'", "").replace(";", "")
        
        try:
            # Check if table exists
            if not await self.check_table_exists(sanitized_table_name):
                raise ValueError(f"Table '{sanitized_table_name}' does not exist")
            
            # Truncate table
            truncate_query = f'TRUNCATE TABLE "{sanitized_table_name}"'
            await self.session.execute(text(truncate_query))
            
            logger.info(f"Successfully truncated table '{sanitized_table_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to truncate table '{sanitized_table_name}': {e}")
            await self.session.rollback()
            raise Exception(f"Truncate operation failed: {e}")