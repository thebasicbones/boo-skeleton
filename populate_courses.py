"""
Populate the database with course structure examples showing multiple DAGs
"""
import asyncio

import httpx

API_BASE = "http://localhost:8000/api"


async def populate_courses():
    """Create course structure examples with multiple DAGs"""

    async with httpx.AsyncClient() as client:
        created_resources = {}

        print("Creating Computer Science Course Structure...")
        print("=" * 60)

        # DAG 1: Computer Science Core Courses
        print("\n📚 DAG 1: Computer Science Core")

        # CS101 - Intro to Programming (no prerequisites)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "CS101 - Intro to Programming",
                "description": "Learn basic programming concepts with Python",
                "dependencies": [],
            },
        )
        cs101 = response.json()
        created_resources["CS101"] = cs101["id"]
        print(f"✓ Created: {cs101['name']}")

        # CS102 - Data Structures (requires CS101)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "CS102 - Data Structures",
                "description": "Arrays, linked lists, trees, and graphs",
                "dependencies": [created_resources["CS101"]],
            },
        )
        cs102 = response.json()
        created_resources["CS102"] = cs102["id"]
        print(f"✓ Created: {cs102['name']} (depends on CS101)")

        # CS201 - Algorithms (requires CS102)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "CS201 - Algorithms",
                "description": "Algorithm design and analysis",
                "dependencies": [created_resources["CS102"]],
            },
        )
        cs201 = response.json()
        created_resources["CS201"] = cs201["id"]
        print(f"✓ Created: {cs201['name']} (depends on CS102)")

        # CS301 - Advanced Algorithms (requires CS201)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "CS301 - Advanced Algorithms",
                "description": "Dynamic programming, graph algorithms, NP-completeness",
                "dependencies": [created_resources["CS201"]],
            },
        )
        cs301 = response.json()
        created_resources["CS301"] = cs301["id"]
        print(f"✓ Created: {cs301['name']} (depends on CS201)")

        # DAG 2: Mathematics Track
        print("\n📐 DAG 2: Mathematics Track")

        # MATH101 - Calculus I (no prerequisites)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "MATH101 - Calculus I",
                "description": "Limits, derivatives, and integrals",
                "dependencies": [],
            },
        )
        math101 = response.json()
        created_resources["MATH101"] = math101["id"]
        print(f"✓ Created: {math101['name']}")

        # MATH201 - Linear Algebra (requires MATH101)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "MATH201 - Linear Algebra",
                "description": "Vectors, matrices, and linear transformations",
                "dependencies": [created_resources["MATH101"]],
            },
        )
        math201 = response.json()
        created_resources["MATH201"] = math201["id"]
        print(f"✓ Created: {math201['name']} (depends on MATH101)")

        # MATH301 - Probability & Statistics (requires MATH201)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "MATH301 - Probability & Statistics",
                "description": "Probability theory and statistical inference",
                "dependencies": [created_resources["MATH201"]],
            },
        )
        math301 = response.json()
        created_resources["MATH301"] = math301["id"]
        print(f"✓ Created: {math301['name']} (depends on MATH201)")

        # DAG 3: Web Development Track
        print("\n🌐 DAG 3: Web Development Track")

        # WEB101 - HTML & CSS (no prerequisites)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "WEB101 - HTML & CSS",
                "description": "Building web pages with HTML and CSS",
                "dependencies": [],
            },
        )
        web101 = response.json()
        created_resources["WEB101"] = web101["id"]
        print(f"✓ Created: {web101['name']}")

        # WEB201 - JavaScript (requires WEB101)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "WEB201 - JavaScript",
                "description": "Client-side programming with JavaScript",
                "dependencies": [created_resources["WEB101"]],
            },
        )
        web201 = response.json()
        created_resources["WEB201"] = web201["id"]
        print(f"✓ Created: {web201['name']} (depends on WEB101)")

        # WEB301 - React & Modern Frameworks (requires WEB201)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "WEB301 - React & Modern Frameworks",
                "description": "Building SPAs with React and modern tools",
                "dependencies": [created_resources["WEB201"]],
            },
        )
        web301 = response.json()
        created_resources["WEB301"] = web301["id"]
        print(f"✓ Created: {web301['name']} (depends on WEB201)")

        # DAG 4: Database Track
        print("\n💾 DAG 4: Database Track")

        # DB101 - Database Fundamentals (no prerequisites)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "DB101 - Database Fundamentals",
                "description": "Relational databases and SQL basics",
                "dependencies": [],
            },
        )
        db101 = response.json()
        created_resources["DB101"] = db101["id"]
        print(f"✓ Created: {db101['name']}")

        # DB201 - Advanced Databases (requires DB101)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "DB201 - Advanced Databases",
                "description": "NoSQL, indexing, and query optimization",
                "dependencies": [created_resources["DB101"]],
            },
        )
        db201 = response.json()
        created_resources["DB201"] = db201["id"]
        print(f"✓ Created: {db201['name']} (depends on DB101)")

        # Cross-DAG Dependencies: Advanced Courses
        print("\n🔗 Creating Cross-DAG Dependencies...")

        # ML401 - Machine Learning (requires CS201, MATH301, and CS102)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "ML401 - Machine Learning",
                "description": "Supervised and unsupervised learning algorithms",
                "dependencies": [
                    created_resources["CS201"],
                    created_resources["MATH301"],
                    created_resources["CS102"],
                ],
            },
        )
        ml401 = response.json()
        created_resources["ML401"] = ml401["id"]
        print(f"✓ Created: {ml401['name']} (depends on CS201, MATH301, CS102)")

        # FULLSTACK401 - Full Stack Development (requires WEB301, DB201, CS102)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "FULLSTACK401 - Full Stack Development",
                "description": "Building complete web applications",
                "dependencies": [
                    created_resources["WEB301"],
                    created_resources["DB201"],
                    created_resources["CS102"],
                ],
            },
        )
        fullstack401 = response.json()
        created_resources["FULLSTACK401"] = fullstack401["id"]
        print(f"✓ Created: {fullstack401['name']} (depends on WEB301, DB201, CS102)")

        print("\n" + "=" * 60)
        print(f"✅ Successfully created {len(created_resources)} courses!")
        print("\n📊 Course Structure Summary:")
        print("  • 4 independent DAGs (CS Core, Math, Web Dev, Database)")
        print("  • 2 advanced courses connecting multiple DAGs")
        print("  • Total depth levels: 0-4")
        print("\n🌐 View at: http://localhost:8000/static/index.html")
        print("=" * 60)

        # Fetch and display topological order
        print("\n📋 Topological Order (from search endpoint):")
        search_response = await client.get(f"{API_BASE}/search")
        if search_response.status_code == 200:
            resources = search_response.json()
            for idx, resource in enumerate(resources, 1):
                deps = len(resource.get("dependencies", []))
                print(f"  {idx:2d}. {resource['name']:<45} ({deps} dependencies)")

        return created_resources


if __name__ == "__main__":
    print("\n🎓 Course Structure Population Script")
    print("=" * 60)
    print("This will create a realistic course prerequisite structure")
    print("demonstrating multiple DAGs and cross-DAG dependencies.")
    print("=" * 60)

    try:
        asyncio.run(populate_courses())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the server is running at http://localhost:8000")
