"""Resource Service for business logic and coordination"""
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_factory import get_repository
from app.exceptions import CircularDependencyError, ResourceNotFoundError, ValidationError
from app.schemas import ResourceCreate, ResourceResponse, ResourceUpdate
from app.services.topological_sort_service import TopologicalSortService


class ResourceService:
    """Service class for resource business logic"""

    def __init__(self, db: AsyncSession | AsyncIOMotorDatabase):
        """
        Initialize service with database session or database instance.

        Args:
            db: Database connection (AsyncSession for SQLite or AsyncIOMotorDatabase for MongoDB)
        """
        self.db = db
        self.repository = get_repository(db)
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
            {"id": self._get_resource_id(r), "dependencies": self._get_resource_dependencies(r)}
            for r in existing_resources
        ]

        # Generate a temporary ID for validation (will be replaced by actual UUID)
        temp_id = "temp_new_resource_id"

        # Validate that adding this resource won't create a cycle
        try:
            self.topo_service.validate_no_cycles(resource_dicts, temp_id, data.dependencies)
        except CircularDependencyError as e:
            raise ValidationError(
                "Cannot create resource: would create circular dependency", {"cycle": str(e)}
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

    async def get_all_resources(self) -> list[ResourceResponse]:
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
                {"id": self._get_resource_id(r), "dependencies": self._get_resource_dependencies(r)}
                for r in all_resources
            ]

            # Validate that updating this resource won't create a cycle
            try:
                self.topo_service.validate_no_cycles(resource_dicts, resource_id, data.dependencies)
            except CircularDependencyError as e:
                raise ValidationError(
                    "Cannot update resource: would create circular dependency", {"cycle": str(e)}
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

    async def search_resources(self, query: str | None = None) -> list[ResourceResponse]:
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
                "id": self._get_resource_id(r),
                "name": self._get_resource_name(r),
                "description": self._get_resource_description(r),
                "dependencies": self._get_resource_dependencies(r),
                "created_at": self._get_resource_created_at(r),
                "updated_at": self._get_resource_updated_at(r),
            }
            for r in resources
        ]

        # Sort topologically
        try:
            sorted_dicts = self.topo_service.topological_sort(resource_dicts)
        except CircularDependencyError as e:
            raise ValidationError(
                "Circular dependency detected in search results", {"cycle": str(e)}
            )

        # Convert back to ResourceResponse
        return [
            ResourceResponse(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                dependencies=r["dependencies"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in sorted_dicts
        ]

    async def _validate_dependencies_exist(self, dependency_ids: list[str]) -> None:
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
                    "Invalid dependency: resource not found", {"dependency_id": dep_id}
                )

    @staticmethod
    def _get_resource_id(resource: dict[str, Any] | Any) -> str:
        """Extract resource ID from either dict or object."""
        return resource["id"] if isinstance(resource, dict) else resource.id

    @staticmethod
    def _get_resource_name(resource: dict[str, Any] | Any) -> str:
        """Extract resource name from either dict or object."""
        return resource["name"] if isinstance(resource, dict) else resource.name

    @staticmethod
    def _get_resource_description(resource: dict[str, Any] | Any) -> str | None:
        """Extract resource description from either dict or object."""
        return resource.get("description") if isinstance(resource, dict) else resource.description

    @staticmethod
    def _get_resource_dependencies(resource: dict[str, Any] | Any) -> list[str]:
        """Extract resource dependencies from either dict or object."""
        if isinstance(resource, dict):
            return resource.get("dependencies", [])
        else:
            return [d.id for d in resource.dependencies]

    @staticmethod
    def _get_resource_created_at(resource: dict[str, Any] | Any):
        """Extract resource created_at from either dict or object."""
        return resource["created_at"] if isinstance(resource, dict) else resource.created_at

    @staticmethod
    def _get_resource_updated_at(resource: dict[str, Any] | Any):
        """Extract resource updated_at from either dict or object."""
        return resource["updated_at"] if isinstance(resource, dict) else resource.updated_at

    def _resource_to_response(self, resource: dict[str, Any] | Any) -> ResourceResponse:
        """
        Convert a resource (dict or model object) to ResourceResponse schema.

        This method works with both MongoDB dictionaries and SQLAlchemy model objects,
        making the service layer backend-agnostic.

        Args:
            resource: Resource data (dict from MongoDB or model object from SQLAlchemy)

        Returns:
            ResourceResponse schema
        """
        return ResourceResponse(
            id=self._get_resource_id(resource),
            name=self._get_resource_name(resource),
            description=self._get_resource_description(resource),
            dependencies=self._get_resource_dependencies(resource),
            created_at=self._get_resource_created_at(resource),
            updated_at=self._get_resource_updated_at(resource),
        )
