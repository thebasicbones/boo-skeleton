"""Populate port 8001 (MongoDB) with course data"""
import asyncio
import httpx

API_BASE = "http://localhost:8001/api"

async def clear_and_populate():
    async with httpx.AsyncClient() as client:
        # First, delete all existing resources
        print("Clearing existing resources...")
        response = await client.get(f"{API_BASE}/resources")
        if response.status_code == 200:
            resources = response.json()
            for resource in resources:
                await client.delete(f"{API_BASE}/resources/{resource['id']}")
            print(f"✓ Cleared {len(resources)} resources")
        
        # Now run the same population logic
        created = {}
        
        print("\n📚 Creating CS Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"CS101 - Intro to Programming","description":"Learn basic programming concepts with Python","dependencies":[]})
        created["CS101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"CS102 - Data Structures","description":"Arrays, linked lists, trees, and graphs","dependencies":[created["CS101"]]})
        created["CS102"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"CS201 - Algorithms","description":"Algorithm design and analysis","dependencies":[created["CS102"]]})
        created["CS201"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"CS301 - Advanced Algorithms","description":"Dynamic programming, graph algorithms, NP-completeness","dependencies":[created["CS201"]]})
        created["CS301"] = r.json()["id"]
        
        print("📐 Creating Math Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"MATH101 - Calculus I","description":"Limits, derivatives, and integrals","dependencies":[]})
        created["MATH101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"MATH201 - Linear Algebra","description":"Vectors, matrices, and linear transformations","dependencies":[created["MATH101"]]})
        created["MATH201"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"MATH301 - Probability & Statistics","description":"Probability theory and statistical inference","dependencies":[created["MATH201"]]})
        created["MATH301"] = r.json()["id"]
        
        print("🌐 Creating Web Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"WEB101 - HTML & CSS","description":"Building web pages with HTML and CSS","dependencies":[]})
        created["WEB101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"WEB201 - JavaScript","description":"Client-side programming with JavaScript","dependencies":[created["WEB101"]]})
        created["WEB201"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"WEB301 - React & Modern Frameworks","description":"Building SPAs with React and modern tools","dependencies":[created["WEB201"]]})
        created["WEB301"] = r.json()["id"]
        
        print("💾 Creating DB Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"DB101 - Database Fundamentals","description":"Relational databases and SQL basics","dependencies":[]})
        created["DB101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"DB201 - Advanced Databases","description":"NoSQL, indexing, and query optimization","dependencies":[created["DB101"]]})
        created["DB201"] = r.json()["id"]
        
        print("🔗 Creating Cross-track Courses...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"ML401 - Machine Learning","description":"Supervised and unsupervised learning algorithms","dependencies":[created["CS201"],created["MATH301"],created["CS102"]]})
        created["ML401"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"FULLSTACK401 - Full Stack Development","description":"Building complete web applications","dependencies":[created["WEB301"],created["DB201"],created["CS102"]]})
        created["FULLSTACK401"] = r.json()["id"]
        
        print("🎨 Creating Art Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"ART101 - Drawing Fundamentals","description":"Basic drawing techniques and principles","dependencies":[]})
        created["ART101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"ART201 - Digital Art","description":"Digital illustration and design","dependencies":[created["ART101"]]})
        created["ART201"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"ART301 - 3D Modeling","description":"3D modeling and animation","dependencies":[created["ART201"]]})
        created["ART301"] = r.json()["id"]
        
        print("🎵 Creating Music Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"MUS101 - Music Theory Basics","description":"Notes, scales, and basic harmony","dependencies":[]})
        created["MUS101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"MUS201 - Advanced Harmony","description":"Chord progressions and voice leading","dependencies":[created["MUS101"]]})
        created["MUS201"] = r.json()["id"]
        
        print("🏃 Creating PE Track...")
        r = await client.post(f"{API_BASE}/resources", json={"name":"PE101 - Fitness Fundamentals","description":"Basic fitness and exercise principles","dependencies":[]})
        created["PE101"] = r.json()["id"]
        
        r = await client.post(f"{API_BASE}/resources", json={"name":"PE201 - Sports Science","description":"Biomechanics and sports physiology","dependencies":[created["PE101"]]})
        created["PE201"] = r.json()["id"]
        
        print(f"\n✅ Created {len(created)} courses on port 8001!")
        print("🌐 View at: http://localhost:8001/static/index.html")

if __name__ == "__main__":
    asyncio.run(clear_and_populate())
