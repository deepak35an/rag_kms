import requests
import time
import json

BASE_URL = "http://localhost:8000"

def simulate_flow():
    print("=" * 60)
    print("🚀 FRONTEND SIMULATOR 🚀")
    print("=" * 60)

    # 1. Health Check (Simulates checking if backend is ready)
    print("\n[1. HEALTH CHECK] Pinging backend /health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is Online:", response.json())
        else:
            print("❌ Backend returned error:", response.status_code)
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error! Is the Uvicorn server running?")
        print("   Please start it in another terminal with: uvicorn main:app --reload")
        return

    # 2. Create Session (Simulates user opening chat)
    print("\n[2. CREATE SESSION] Requesting new chat session...")
    response = requests.post(f"{BASE_URL}/create_session")
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data.get("session_id")
        print(f"✅ Session Created! ID: {session_id}")
    else:
        print("❌ Failed to create session.")
        return

    # 3. Ask a Question (Simulates user sending a message)
    question = "What are the participating institutes?"
    print(f"\n[3. ASK QUESTION] Sending question: '{question}'")
    
    payload = {
        "question": question,
        "session_id": session_id
    }
    
    print("⏳ Waiting for backend to retrieve context and generate response (this might take a few seconds)...")
    start_time = time.time()
    
    # We use a POST request to the /ask endpoint
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    end_time = time.time()
    
    if response.status_code == 200:
        result = response.json()
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print("\n" + "=" * 40)
        print("🤖 BACKEND RESPONSE:")
        print("=" * 40)
        print(result.get("response"))
        
        print("\n" + "=" * 40)
        print("📚 SOURCES (Sent to frontend for UI rendering):")
        print("=" * 40)
        for doc in result.get("sources", []):
            print(f"- {doc.get('source')} (Page {doc.get('page')}) - Relevance: {doc.get('relevance'):.2f}")
    else:
        print("❌ Failed to get answer:", response.text)

if __name__ == "__main__":
    simulate_flow()
