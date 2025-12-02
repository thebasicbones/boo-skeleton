"""SQLAlchemy resource repository for database operations"""
from typing import List, Optional
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.sqlalchemy_resource import Resource
from app.schemas import ResourceCreate, ResourceUpdate
from app.repositories.base_resource_repository import BaseResourceRepository


class SQLAlchemyResourceRepository(BaseResourceRepository):
    """SQLAlchemy implementation of the resource repository interface"""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session"""
        self.db = db
    
    async def get_all(self) -> List[Resource]:
        """
        Retrieve all resources with their dependencies loaded.
        
        Returns:
            List of all Resource objects with dependencies eagerly loaded
        """
        result = await self.db.execute(
            select(Resource).options(selectinload(Resource.dependencies))
        )
        return list(result.scalars().all())
    
    async def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """
        Retrieve a single resource by ID with dependencies loaded.
        
        Args:
            resource_id: The unique identifier of the resource
            
        Returns:
            Resource object if found, None otherwise
        """
        result = await self.db.execute(
            select(Resource)
            .options(selectinload(Resource.dependencies))
            .where(Resource.id == resource_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, data: ResourceCreate) -> Resource:
        """
        Create a new resource in the database.
        
        Args:
            data: ResourceCreate schema with resource data
            
        Returns:
            The newly created Resource object
        """
        # Create the resource instance
        resource = Resource(
            name=data.name,
            description=data.description
        )
        
        # Add dependencies if provided
        if data.dependencies:
            # Fetch dependency resources
            result = await self.db.execute(
                select(Resource).where(Resource.id.in_(data.dependencies))
            )
            dependency_resources = list(result.scalars().all())
            resource.dependencies = dependency_resources
        
        self.db.add(resource)
        await self.db.commit()
        await self.db.refresh(resource)
        
        # Ensure dependencies are loaded
        await self.db.refresh(resource, ['dependencies'])
        
        return resource
    
    async def update(self, resource_id: str, data: ResourceUpdate) -> Optional[Resource]:
        """
        Update an existing resource.
        
        Args:
            resource_id: The unique identifier of the resource to update
            data: ResourceUpdate schema with updated data
            
        Returns:
            Updated Resource object if found, None otherwise
        """
        # Fetch the resource
        resource = await self.get_by_id(resource_id)
        if not resource:
            return None
        
        # Update fields if provided
        if data.name is not None:
            resource.name = data.name
        if data.description is not None:
            resource.description = data.description
        
        # Update dependencies if provided
        if data.dependencies is not None:
            if data.dependencies:
                # Fetch new dependency resources
                result = await self.db.execute(
                    select(Resource).where(Resource.id.in_(data.dependencies))
                )
                dependency_resources = list(result.scalars().all())
                resource.dependencies = dependency_resources
            else:
                # Clear all dependencies
                resource.dependencies = []
        
        await self.db.commit()
        await self.db.refresh(resource)
        
        # Ensure dependencies are loaded
        await self.db.refresh(resource, ['dependencies'])
        
        return resource
    
    async def delete(self, resource_id: str, cascade: bool = False) -> bool:
        """
        Delete a resource from the database.
        
        Args:
            resource_id: The unique identifier of the resource to delete
            cascade: If True, delete all resources that depend on this resource
            
        Returns:
            True if resource was deleted, False if not found
        """
        # Fetch the resource
        resource = await self.get_by_id(resource_id)
        if not resource:
            return False
        
        if cascade:
            # Find all resources that depend on this one (directly or transitively)
            dependents_to_delete = await self._get_all_dependents(resource_id)
            
            # Delete all dependents first
            for dependent_id in dependents_to_delete:
                await self.db.execute(
                    delete(Resource).where(Resource.id == dependent_id)
                )
        
        # Delete the resource itself
        # The CASCADE on foreign keys will automatically remove junction table entries
        await self.db.delete(resource)
        await self.db.commit()
        
        return True
    
    async def _get_all_dependents(self, resource_id: str) -> List[str]:
        """
        Get all resources that depend on the given resource (transitively).
        
        Args:
            resource_id: The resource ID to find dependents for
            
        Returns:
            List of resource IDs that depend on this resource
        """
        all_dependents = set()
        to_process = [resource_id]
        
        while to_process:
            current_id = to_process.pop(0)
            
            # Find direct dependents
            result = await self.db.execute(
                select(Resource)
                .options(selectinload(Resource.dependencies))
                .where(Resource.dependencies.any(Resource.id == current_id))
            )
            direct_dependents = list(result.scalars().all())
            
            for dependent in direct_dependents:
                if dependent.id not in all_dependents:
                    all_dependents.add(dependent.id)
                    to_process.append(dependent.id)
        
        return list(all_dependents)
    
    async def search(self, query: Optional[str] = None) -> List[Resource]:
        """
        Search for resources by name or description.
        
        Args:
            query: Search string to match against name or description.
                   If None or empty, returns all resources.
            
        Returns:
            List of matching Resource objects with dependencies loaded
        """
        stmt = select(Resource).options(selectinload(Resource.dependencies))
        
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Resource.name.ilike(search_term),
                    Resource.description.ilike(search_term)
                )
            )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
