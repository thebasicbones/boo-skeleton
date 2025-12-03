"""
Add independent DAGs to demonstrate multiple DAG grouping
"""
import asyncio

import httpx

API_BASE = "http://localhost:8000/api"


async def add_independent_dags():
    """Create additional independent DAGs"""

    async with httpx.AsyncClient() as client:
        print("\n🎨 Adding Independent DAG: Art & Design Track")
        print("=" * 60)

        # Art DAG (completely independent)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "ART101 - Drawing Fundamentals",
                "description": "Basic drawing techniques and principles",
                "dependencies": [],
            },
        )
        art101 = response.json()
        print(f"✓ Created: {art101['name']}")

        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "ART201 - Digital Art",
                "description": "Digital illustration and design",
                "dependencies": [art101["id"]],
            },
        )
        art201 = response.json()
        print(f"✓ Created: {art201['name']}")

        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "ART301 - 3D Modeling",
                "description": "3D modeling and animation",
                "dependencies": [art201["id"]],
            },
        )
        art301 = response.json()
        print(f"✓ Created: {art301['name']}")

        print("\n🎵 Adding Independent DAG: Music Theory Track")
        print("=" * 60)

        # Music DAG (completely independent)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "MUS101 - Music Theory Basics",
                "description": "Notes, scales, and basic harmony",
                "dependencies": [],
            },
        )
        mus101 = response.json()
        print(f"✓ Created: {mus101['name']}")

        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "MUS201 - Advanced Harmony",
                "description": "Chord progressions and voice leading",
                "dependencies": [mus101["id"]],
            },
        )
        mus201 = response.json()
        print(f"✓ Created: {mus201['name']}")

        print("\n🏃 Adding Independent DAG: Physical Education Track")
        print("=" * 60)

        # PE DAG (completely independent)
        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "PE101 - Fitness Fundamentals",
                "description": "Basic fitness and exercise principles",
                "dependencies": [],
            },
        )
        pe101 = response.json()
        print(f"✓ Created: {pe101['name']}")

        response = await client.post(
            f"{API_BASE}/resources",
            json={
                "name": "PE201 - Sports Science",
                "description": "Biomechanics and sports physiology",
                "dependencies": [pe101["id"]],
            },
        )
        pe201 = response.json()
        print(f"✓ Created: {pe201['name']}")

        print("\n" + "=" * 60)
        print("✅ Added 3 independent DAGs with 7 new courses!")
        print("\n📊 You should now see 4 separate DAG groups:")
        print("  1. Computer Science + Math + Web + DB (14 courses)")
        print("  2. Art & Design (3 courses)")
        print("  3. Music Theory (2 courses)")
        print("  4. Physical Education (2 courses)")
        print("\n🌐 Refresh: http://localhost:8000/static/index.html")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(add_independent_dags())
