"""
Abstract base service class with validation methods.
Provides business logic layer between API and CRUD.
"""
import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base_crud import BaseCRUD

logger = logging.getLogger(__name__)

CRUDType = TypeVar("CRUDType", bound=BaseCRUD)


class BaseService(ABC, Generic[CRUDType]):
    """
    Abstract base service class.
    Implements business logic and orchestrates CRUD operations.

    Type Parameters:
        CRUDType: CRUD class type
    """

    def __init__(self, crud: CRUDType):
        """
        Initialize service with CRUD instance.

        Args:
            crud: CRUD instance for database operations
        """
        self.crud = crud
        self.service_name = self.__class__.__name__
        logger.info(f"Initialized {self.service_name}")

    @abstractmethod
    async def validate_create(self, db: AsyncSession, obj_in: any) -> bool:
        """
        Validate object before creation.
        Must be implemented by subclasses.

        Args:
            db: Database session
            obj_in: Input object

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    async def validate_update(self, db: AsyncSession, id: int, obj_in: any) -> bool:
        """
        Validate object before update.
        Must be implemented by subclasses.

        Args:
            db: Database session
            id: Object ID
            obj_in: Input object

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        pass

    async def validate_delete(self, db: AsyncSession, id: int) -> bool:
        """
        Validate object before deletion.
        Default implementation allows all deletes.
        Override in subclass for custom logic.

        Args:
            db: Database session
            id: Object ID

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"{self.service_name}: Validating delete for id={id}")
        return True
