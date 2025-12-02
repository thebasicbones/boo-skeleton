# Building a Dependency-Aware CRUD API with FastAPI and Topological Sorting

When building modern web applications, managing relationships between data entities is a common challenge. But what happens when those relationships form a dependency graph, and you need to process items in the correct order? That's exactly the problem I tackled in my latest project: a FastAPI backend that combines traditional CRUD operations with intelligent dependency ordering using topological sorting.

## The Problem: More Than Just CRUD

Most CRUD APIs are straightforward—create, read, update, and delete resources. But in many real-world scenarios, resources depend on each other. Think about:

- **Build systems** where modules depend on other modules
- **Task management** where tasks have prerequisites
- **Package managers** where libraries depend on other libraries
- **Workflow engines** where steps must execute in order

The challenge isn't just storing these relationships—it's ensuring they're processed in the right order and preventing circular dependencies that would break the system.

## The Solution: Topological Sorting Meets REST

I built a full-stack application that elegantly solves this problem by combining:

1. **FastAPI** for high-performance async request handling
2. **SQLAlchemy ORM** for flexible database operations
3. **Kahn's Algorithm** for topological sorting
4. **A clean web interface** for visualizing dependencies

### Architecture Overview

The system follows a layered architecture:

```
Frontend (HTML/CSS/JS)
        ↓
API Layer (FastAPI Routers)
        ↓
Business Logic (Services)
        ↓
Data Access (Repositories)
        ↓
Database (SQLite)
```

Each layer has a clear responsibility, making the codebase maintainable and testable.

## Key Features

### 1. Standard CRUD Operations

The API provides six RESTful endpoints:

- `POST /api/resources` - Create a new resource
- `GET /api/resources` - List all resources
- `GET /api/resources/{id}` - Get a specific resource
- `PUT /api/resources/{id}` - Update a resource
- `DELETE /api/resources/{id}` - Delete a resource
- `GET /api/search` - Search with topological ordering

Each endpoint includes proper validation, error handling, and follows REST conventions with appropriate HTTP status codes.

### 2. Dependency Management

Resources can declare dependencies on other resources. The system maintains these relationships in a junction table, creating a directed graph structure. When you create or update a resource, the system validates that no circular dependencies would be introduced.

### 3. Topological Sorting

The real magic happens in the search endpoint. Using Kahn's Algorithm, the system orders resources so that dependencies always appear before their dependents. This is crucial for any workflow where processing order matters.

**How it works:**

1. Calculate the in-degree (number of dependencies) for each resource
2. Start with resources that have no dependencies
3. Process each resource and "remove" it from the graph
4. Continue until all resources are ordered
5. If any resources remain, a circular dependency exists

The algorithm runs in O(V + E) time, where V is the number of resources and E is the number of dependency relationships—efficient even for large graphs.

### 4. Circular Dependency Detection

One of the trickiest aspects was preventing circular dependencies. The system validates the entire dependency graph before any create or update operation:

```python
# Example of what gets rejected:
Resource A depends on Resource B
Resource B depends on Resource C
Resource C depends on Resource A  # ❌ Circular!
```

When a cycle is detected, the API returns a clear error message showing the cycle path, making it easy to understand and fix the issue.

### 5. Cascade Delete Options

Deleting resources with dependencies requires careful handling. The system offers two modes:

- **Cascade delete**: Remove the resource and all downstream dependents
- **Non-cascade delete**: Remove only the specified resource, updating dependent resources

This flexibility ensures you can manage your data graph safely without accidentally breaking relationships.

## The Frontend Experience

The web interface provides an intuitive way to interact with the system:

- **Visual dependency indicators** show which resources depend on others
- **Search bar** triggers topological sorting in real-time
- **CRUD forms** with dependency selection
- **Delete confirmation** with cascade options
- **Error messages** displayed clearly for validation issues

All built with vanilla JavaScript—no heavy frameworks needed for this use case.

## Testing for Correctness

Building a system that manages complex relationships requires rigorous testing. I implemented a dual testing strategy:

### Unit Tests
Traditional tests for specific scenarios and edge cases using pytest.

### Property-Based Tests
Using Hypothesis, I wrote tests that verify universal properties across randomly generated inputs:

- **Round-trip consistency**: Create then read returns equivalent data
- **Topological ordering**: Dependencies always appear before dependents
- **Cascade delete correctness**: All downstream resources are removed
- **Error format consistency**: All errors follow the same structure

Each property test runs 100+ iterations with random data, catching edge cases that manual tests might miss.

## Real-World Applications

This architecture pattern is useful for:

- **CI/CD pipelines** managing build dependencies
- **Content management systems** with content relationships
- **Project management tools** with task dependencies
- **Infrastructure as code** with resource dependencies
- **Course prerequisites** in educational platforms

## Technical Highlights

**FastAPI's async capabilities** make the API blazingly fast, handling multiple requests concurrently without blocking.

**Pydantic validation** ensures data integrity at the API boundary, catching errors before they reach the database.

**SQLAlchemy's relationship handling** makes working with the dependency graph natural and Pythonic.

**The repository pattern** abstracts database operations, making it easy to swap SQLite for PostgreSQL in production.

## Lessons Learned

1. **Graph algorithms in web APIs** aren't as scary as they sound—Kahn's algorithm is surprisingly straightforward to implement.

2. **Validation is critical** when dealing with user-defined relationships. Preventing circular dependencies upfront saves headaches later.

3. **Property-based testing** is incredibly powerful for systems with complex invariants. It found edge cases I never would have thought to test manually.

4. **Clear error messages** matter. When a circular dependency is detected, showing the actual cycle path helps users fix the issue quickly.

5. **Layered architecture** pays off. Separating concerns made testing easier and the codebase more maintainable.

## What's Next?

Potential enhancements for this system:

- **Batch operations** for creating multiple dependent resources atomically
- **Dependency visualization** with interactive graph rendering
- **Version history** to track changes to the dependency graph over time
- **Performance optimization** with caching for frequently accessed dependency chains
- **WebSocket support** for real-time updates when dependencies change

## Conclusion

Building a CRUD API with dependency management and topological sorting was a fascinating challenge that combined web development, graph algorithms, and rigorous testing practices. The result is a robust system that handles complex relationships gracefully while maintaining data integrity.

The key takeaway? Don't shy away from incorporating computer science fundamentals into your web applications. Algorithms like topological sorting have practical applications beyond academic exercises, and modern frameworks like FastAPI make them easy to implement and deploy.

If you're building a system where order matters and relationships are complex, consider this architecture pattern. The investment in proper dependency management pays dividends in system reliability and user experience.

---

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, SQLite, Hypothesis, Pytest, HTML/CSS/JavaScript

**Source Code:** [Link to your repository]

**Live Demo:** [Link to your demo if available]

---

*Have you built systems with complex dependencies? What challenges did you face? Let me know in the comments!*
