"""Resource Service for business logic and coordination"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.resource_repository import ResourceRepository
from app.services.topological_sort_service import TopologicalSortService, CircularDependencyError
from app.schemas import ResourceCreate, ResourceUpdate, ResourceResponse
from app.models.resource import Resource


class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found"""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource not found: {resource_id}")


class ValidationError(Exception):
    """Exception raised when validation fails"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ResourceService:
    """Service class for resource business logic"""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session"""
        self.db = db
        self.repository = ResourceRepository(db)
        self.topo_service = TopologicalSortService()
    
    async def create_resource(self, data: ResourceCreate) -> ResourceResponse:
        """
        Create a new resource with circular dependency validation.
        
        Args:
            data: ResourceCreate schema with resource data
            
        Returns:
            ResourceResponse with the created resource
            
        Raises:
            ValidationError: If dependencies are invalid or would create a cycle
        """
        # Validate that all dependency IDs exist
        if data.dependencies:
            await self._validate_dependencies_exist(data.dependencies)
        
        # Get all existing resources to validate no cycles
        existing_resources = await self.repository.get_all()
        
        # Convert to dict format for topological sort validation
        resource_dicts = [
            {
                'id': r.id,
                'dependencies': [d.id for d in r.dependencies]
            }
            for r in existing_resources
        ]
        
        # Generate a temporary ID for validation (will be replaced by actual UUID)
        temp_id = "temp_new_resource_id"
        
        # Validate that adding this resource won't create a cycle
        try:
            self.topo_service.validate_no_cycles(
                resource_dicts,
                temp_id,
                data.dependencies
            )
        except CircularDependencyError as e:
            raise ValidationError(
                "Cannot create resource: would create circular dependency",
                {"cycle": str(e)}
            )
        
        # Create the resource
        resource = await self.repository.create(data)
        
        return self._resource_to_response(resource)
    
    async def get_resource(self, resource_id: str) -> ResourceResponse:
        """
        Get a single resource by ID.
        
        Args:
            resource_id: The unique identifier of the resource
            
        Returns:
            ResourceResponse with the resource data
            
        Raises:
            ResourceNotFoundError: If resource doesn't exist
        """
        resource = await self.repository.get_by_id(resource_id)
        
        if not resource:
            raise ResourceNotFoundError(resource_id)
        
        return self._resource_to_response(resource)
    
    async def get_all_resources(self) -> List[ResourceResponse]:
        """
        Get all resources.
        
        Returns:
            List of ResourceResponse objects
        """
        resources = await self.repository.get_all()
        return [self._resource_to_response(r) for r in resources]
    
    async def update_resource(self, resource_id: str, data: ResourceUpdate) -> ResourceResponse:
        """
        Update an existing resource with dependency validation.
        
        Args:
            resource_id: The unique identifier of the resource to update
            data: ResourceUpdate schema with updated data
            
        Returns:
            ResourceResponse with the updated resource
            
        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ValidationError: If dependencies are invalid or would create a cycle
        """
        # Check if resource exists
        existing_resource = await self.repository.get_by_id(resource_id)
        if not existing_resource:
            raise ResourceNotFoundError(resource_id)
        
        # Validate that all dependency IDs exist (if dependencies are being updated)
        if data.dependencies is not None:
            await self._validate_dependencies_exist(data.dependencies)
            
            # Get all existing resources to validate no cycles
            all_resources = await self.repository.get_all()
            
            # Convert to dict format for topological sort validation
            resource_dicts = [
                {
                    'id': r.id,
                    'dependencies': [d.id for d in r.dependencies]
                }
                for r in all_resources
            ]
            
            # Validate that updating this resource won't create a cycle
            try:
                self.topo_service.validate_no_cycles(
                    resource_dicts,
                    resource_id,
                    data.dependencies
                )
            except CircularDependencyError as e:
                raise ValidationError(
                    "Cannot update resource: would create circular dependency",
                    {"cycle": str(e)}
                )
        
        # Update the resource
        updated_resource = await self.repository.update(resource_id, data)
        
        return self._resource_to_response(updated_resource)
    
    async def delete_resource(self, resource_id: str, cascade: bool = False) -> None:
        """
        Delete a resource with optional cascade.
        
        Args:
            resource_id: The unique identifier of the resource to delete
            cascade: If True, delete all resources that depend on this resource
            
        Raises:
            ResourceNotFoundError: If resource doesn't exist
        """
        success = await self.repository.delete(resource_id, cascade)
        
        if not success:
            raise ResourceNotFoundError(resource_id)
    
    async def search_resources(self, query: Optional[str] = None) -> List[ResourceResponse]:
        """
        Search for resources and return them in topological order.
        
        Args:
            query: Search string to match against name or description.
                   If None or empty, returns all resources.
            
        Returns:
            List of ResourceResponse objects in topological order
            
        Raises:
            ValidationError: If circular dependency is detected in results
        """
        # Search for matching resources
        resources = await self.repository.search(query)
        
        if not resources:
            return []
        
        # Convert to dict format for topological sort
        resource_dicts = [
            {
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'dependencies': [d.id for d in r.dependencies],
                'created_at': r.created_at,
                'updated_at': r.updated_at
            }
            for r in resources
        ]
        
        # Sort topologically
        try:
            sorted_dicts = self.topo_service.topological_sort(resource_dicts)
        except CircularDependencyError as e:
            raise ValidationError(
                "Circular dependency detected in search results",
                {"cycle": str(e)}
            )
        
        # Convert back to ResourceResponse
        return [
            ResourceResponse(
                id=r['id'],
                name=r['name'],
                description=r['description'],
                dependencies=r['dependencies'],
                created_at=r['created_at'],
                updated_at=r['updated_at']
            )
            for r in sorted_dicts
        ]
    
    async def _validate_dependencies_exist(self, dependency_ids: List[str]) -> None:
        """
        Validate that all dependency IDs exist in the database.
        
        Args:
            dependency_ids: List of resource IDs to validate
            
        Raises:
            ValidationError: If any dependency ID doesn't exist
        """
        if not dependency_ids:
            return
        
        # Check each dependency
        for dep_id in dependency_ids:
            resource = await self.repository.get_by_id(dep_id)
            if not resource:
                raise ValidationError(
                    f"Invalid dependency: resource not found",
                    {"dependency_id": dep_id}
                )
    
    @staticmethod
    def _resource_to_response(resource: Resource) -> ResourceResponse:
        """
        Convert a Resource model to ResourceResponse schema.
        
        Args:
            resource: Resource model instance
            
        Returns:
            ResourceResponse schema
        """
        return ResourceResponse(
            id=resource.id,
            name=resource.name,
            description=resource.description,
            dependencies=[d.id for d in resource.dependencies],
            created_at=resource.created_at,
            updated_at=resource.updated_at
        )
