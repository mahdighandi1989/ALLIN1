from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, MetaData, Table
from sqlalchemy.sql import select, func
from typing import Dict, Any, List, Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for common database operations with enhanced security"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _validate_identifier(self, identifier: str) -> str:
        """Validate and sanitize SQL identifiers (table/column names)"""
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        
        # Remove any whitespace
        identifier = identifier.strip()
        
        # Check for valid SQL identifier pattern
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid identifier: {identifier}. Must contain only letters, numbers, and underscores, starting with letter or underscore")
        
        # Check length (PostgreSQL limit is 63 characters)
        if len(identifier) > 63:
            raise ValueError(f"Identifier too long: {identifier}. Maximum 63 characters allowed")
        
        # Check against SQL reserved words (basic list)
        reserved_words = {
            'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter', 
            'table', 'index', 'view', 'database', 'schema', 'user', 'grant',
            'revoke', 'commit', 'rollback', 'transaction', 'where', 'from',
            'join', 'union', 'order', 'group', 'having', 'limit', 'offset'
        }
        
        if identifier.lower() in reserved_words:
            raise ValueError(f"Reserved word cannot be used as identifier: {identifier}")
        
        return identifier
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a parameterized SQL query and return results"""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        try:
            result = await self.session.execute(text(query), params or {})
            rows = result.fetchall()
            
            if rows:
                # Get column names from the result
                columns = list(result.keys())
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    async def execute_scalar(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a parameterized query and return a single scalar value"""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        try:
            result = await self.session.execute(text(query), params or {})
            return result.scalar()
        except Exception as e:
            logger.error(f"Database scalar query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        validated_table_name = self._validate_identifier(table_name)
        
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = :table_name
            AND table_schema = CURRENT_SCHEMA()
        );
        """
        
        try:
            result = await self.execute_scalar(query, {"table_name": validated_table_name})
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking table existence for {validated_table_name}: {e}")
            raise
    
    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        validated_table_name = self._validate_identifier(table_name)
        
        query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_name = :table_name
        AND table_schema = CURRENT_SCHEMA()
        ORDER BY ordinal_position;
        """
        
        try:
            return await self.execute_query(query, {"table_name": validated_table_name})
        except Exception as e:
            logger.error(f"Error getting columns for table {validated_table_name}: {e}")
            raise
    
    async def backup_table(self, table_name: str, backup_suffix: str = "backup") -> str:
        """Create a backup of a table using safe SQL construction"""
        validated_table_name = self._validate_identifier(table_name)
        validated_suffix = self._validate_identifier(backup_suffix)
        
        # Check if source table exists
        if not await self.check_table_exists(validated_table_name):
            raise ValueError(f"Source table '{validated_table_name}' does not exist")
        
        # Generate backup table name with timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table_name = f"{validated_table_name}_{validated_suffix}_{timestamp}"
        
        # Validate the full backup table name
        backup_table_name = self._validate_identifier(backup_table_name)
        
        # Check if backup table already exists
        if await self.check_table_exists(backup_table_name):
            raise ValueError(f"Backup table '{backup_table_name}' already exists")
        
        try:
            # Use parameterized query with identifier validation
            # Note: For CREATE TABLE AS, we need to use text() with validated identifiers
            # since table names cannot be parameterized in PostgreSQL
            query = text(f"CREATE TABLE {backup_table_name} AS SELECT * FROM {validated_table_name}")
            
            await self.session.execute(query)
            await self.session.commit()
            
            logger.info(f"Successfully created backup table: {backup_table_name}")
            return backup_table_name
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating backup table: {e}")
            raise
    
    async def get_table_row_count(self, table_name: str) -> int:
        """Get the number of rows in a table"""
        validated_table_name = self._validate_identifier(table_name)
        
        # Check if table exists first
        if not await self.check_table_exists(validated_table_name):
            raise ValueError(f"Table '{validated_table_name}' does not exist")
        
        try:
            # Use text() with validated identifier for COUNT query
            query = text(f"SELECT COUNT(*) FROM {validated_table_name}")
            result = await self.session.execute(query)
            count = result.scalar()
            return int(count) if count is not None else 0
            
        except Exception as e:
            logger.error(f"Error getting row count for table {validated_table_name}: {e}")
            raise
    
    async def get_table_size(self, table_name: str) -> Dict[str, Any]:
        """Get table size information"""
        validated_table_name = self._validate_identifier(table_name)
        
        query = """
        SELECT 
            pg_size_pretty(pg_total_relation_size(:table_name::regclass)) as total_size,
            pg_size_pretty(pg_relation_size(:table_name::regclass)) as table_size,
            pg_size_pretty(pg_total_relation_size(:table_name::regclass) - pg_relation_size(:table_name::regclass)) as index_size
        """
        
        try:
            result = await self.execute_query(query, {"table_name": validated_table_name})
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error getting table size for {validated_table_name}: {e}")
            raise
    
    async def analyze_table(self, table_name: str) -> None:
        """Run ANALYZE on a table to update statistics"""
        validated_table_name = self._validate_identifier(table_name)
        
        if not await self.check_table_exists(validated_table_name):
            raise ValueError(f"Table '{validated_table_name}' does not exist")
        
        try:
            query = text(f"ANALYZE {validated_table_name}")
            await self.session.execute(query)
            await self.session.commit()
            logger.info(f"Successfully analyzed table: {validated_table_name}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error analyzing table {validated_table_name}: {e}")
            raise
    
    async def vacuum_table(self, table_name: str, full: bool = False) -> None:
        """Run VACUUM on a table"""
        validated_table_name = self._validate_identifier(table_name)
        
        if not await self.check_table_exists(validated_table_name):
            raise ValueError(f"Table '{validated_table_name}' does not exist")
        
        try:
            # VACUUM cannot be run inside a transaction, so we need to handle this carefully
            vacuum_type = "VACUUM FULL" if full else "VACUUM"
            query = text(f"{vacuum_type} {validated_table_name}")
            
            # Note: VACUUM requires autocommit mode in some cases
            await self.session.execute(query)
            logger.info(f"Successfully vacuumed table: {validated_table_name}")
            
        except Exception as e:
            logger.error(f"Error vacuuming table {validated_table_name}: {e}")
            raise
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get general database statistics"""
        query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname = CURRENT_SCHEMA()
        LIMIT 100;
        """
        
        try:
            stats = await self.execute_query(query)
            
            # Get database size
            size_query = "SELECT pg_size_pretty(pg_database_size(current_database())) as db_size"
            size_result = await self.execute_query(size_query)
            
            return {
                "database_size": size_result[0]["db_size"] if size_result else "Unknown",
                "table_stats": stats,
                "total_tables": len(set(stat["tablename"] for stat in stats))
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            raise
    
    async def drop_table_safely(self, table_name: str, cascade: bool = False) -> None:
        """Safely drop a table with validation"""
        validated_table_name = self._validate_identifier(table_name)
        
        if not await self.check_table_exists(validated_table_name):
            raise ValueError(f"Table '{validated_table_name}' does not exist")
        
        # Additional safety check - prevent dropping core tables
        protected_tables = {"users", "customers", "facilities", "alembic_version"}
        if validated_table_name.lower() in protected_tables:
            raise ValueError(f"Cannot drop protected table: {validated_table_name}")
        
        try:
            cascade_clause = " CASCADE" if cascade else ""
            query = text(f"DROP TABLE {validated_table_name}{cascade_clause}")
            
            await self.session.execute(query)
            await self.session.commit()
            logger.info(f"Successfully dropped table: {validated_table_name}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error dropping table {validated_table_name}: {e}")
            raise