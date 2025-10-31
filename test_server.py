"""
Simple script to test if the backend server is running and responding.
Run this to diagnose connection issues.
"""
import requests
import sys

API_BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        print(f"✓ Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the backend is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_register():
    """Test registration endpoint"""
    try:
        # Use a unique username each time
        import random
        test_user = f"testuser{random.randint(1000, 9999)}"
        data = {
            "username": test_user,
            "email": f"{test_user}@test.com",
            "password": "Test123!",
            "full_name": "Test User"
        }
        response = requests.post(f"{API_BASE_URL}/api/auth/register", json=data)
        print(f"✓ Register test: {response.status_code}")
        if response.status_code == 201:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Response: {response.text}")
        return response.status_code in [201, 400]  # 400 might mean user exists, which is ok
    except Exception as e:
        print(f"✗ Register test failed: {e}")
        return False

def test_login():
    """Test login with admin credentials"""
    try:
        data = {
            "login": "admin",
            "password": "Admin@123"
        }
        response = requests.post(f"{API_BASE_URL}/api/auth/login", json=data)
        print(f"✓ Login test: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Token received: {result.get('access_token', 'No token')[:20]}...")
            print(f"  User: {result.get('user', {}).get('username', 'Unknown')}")
        else:
            print(f"  Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing backend server connection...")
    print("=" * 50)
    
    health_ok = test_health()
    if not health_ok:
        print("\n❌ Server is not running or not accessible.")
        print("\nTo start the server, run:")
        print("  cd project")
        print("  python -m backend.app")
        sys.exit(1)
    
    print()
    test_register()
    print()
    test_login()
    
    print("\n" + "=" * 50)
    print("If all tests pass, your server is working correctly!")
    print("If tests fail, check the error messages above.")

