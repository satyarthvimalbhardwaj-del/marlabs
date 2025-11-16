"""
Abstract base CRUD with comprehensive error handling and logging.
"""
import logging
from abc import ABC
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel
from app.database import Base
from app.core.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Abstract base class for CRUD operations with async support.

    Provides:
    - Standard CRUD operations (Create, Read, Update, Delete)
    - Pagination and filtering
    - Error handling and logging
    - Transaction management
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD with model class.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self.model_name = model.__name__
        logger.info(f"Initialized {self.model_name}CRUD")

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            db: Database session
            id: Record ID

        Returns:
            Model instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching {self.model_name} with id={id}")
            result = await db.execute(
                select(self.model).where(self.model.id == id)
            )
            obj = result.scalar_one_or_none()

            if obj:
                logger.debug(f"{self.model_name} id={id} found")
            else:
                logger.debug(f"{self.model_name} id={id} not found")

            return obj
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching {self.model_name} id={id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch {self.model_name}", details={"id": id, "error": str(e)})

    async def get_multi(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
            order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            filters: Filter dictionary
            order_by: Column name for ordering

        Returns:
            List of model instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching {self.model_name} list: skip={skip}, limit={limit}, filters={filters}")
            query = select(self.model)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        query = query.where(getattr(self.model, key) == value)

            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by).desc())
            else:
                query = query.order_by(self.model.id.desc())

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            objects = result.scalars().all()

            logger.debug(f"Retrieved {len(objects)} {self.model_name} records")
            return list(objects)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching {self.model_name} list: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch {self.model_name} list", details={"error": str(e)})

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            db: Database session
            obj_in: Pydantic schema with data

        Returns:
            Created model instance

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            obj_data = obj_in.model_dump()
            logger.info(f"Creating {self.model_name}: {obj_data}")

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            logger.info(f"{self.model_name} created successfully: id={db_obj.id}")
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error creating {self.model_name}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Duplicate or invalid data for {self.model_name}", details={"error": str(e)})
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating {self.model_name}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to create {self.model_name}", details={"error": str(e)})

    async def update(
            self,
            db: AsyncSession,
            id: int,
            obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """
        Update an existing record.

        Args:
            db: Database session
            id: Record ID
            obj_in: Pydantic schema with update data

        Returns:
            Updated model instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Updating {self.model_name} id={id}")

            db_obj = await self.get(db, id)
            if not db_obj:
                logger.warning(f"{self.model_name} id={id} not found for update")
                return None

            update_data = obj_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_obj, field, value)

            await db.commit()
            await db.refresh(db_obj)

            logger.info(f"{self.model_name} id={id} updated successfully")
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error updating {self.model_name} id={id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Duplicate or invalid data for {self.model_name}", details={"id": id, "error": str(e)})
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating {self.model_name} id={id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to update {self.model_name}", details={"id": id, "error": str(e)})

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            db: Database session
            id: Record ID

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Deleting {self.model_name} id={id}")

            db_obj = await self.get(db, id)
            if not db_obj:
                logger.warning(f"{self.model_name} id={id} not found for deletion")
                return False

            await db.delete(db_obj)
            await db.commit()

            logger.info(f"{self.model_name} id={id} deleted successfully")
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error deleting {self.model_name} id={id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to delete {self.model_name}", details={"id": id, "error": str(e)})

    async def count(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters.

        Args:
            db: Database session
            filters: Optional filter dictionary

        Returns:
            Total count

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(func.count(self.model.id))

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        query = query.where(getattr(self.model, key) == value)

            result = await db.execute(query)
            count = result.scalar()

            logger.debug(f"{self.model_name} count: {count} (filters={filters})")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error counting {self.model_name}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to count {self.model_name}", details={"error": str(e)})
