import urllib.request
import urllib.error
import json
import os

API_BASE = "http://127.0.0.1:8000"

def login():
    login_data = json.dumps({"username": "admin", "password": "admin123"}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result.get("access_token")
    except urllib.error.HTTPError as e:
        print(f"Login failed: {e.code} - {e.read().decode()}")
        return None

def test_endpoint(token, endpoint, method="GET", body=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if body:
        data = json.dumps(body).encode("utf-8")
    else:
        data = None
    req = urllib.request.Request(f"{API_BASE}{endpoint}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"{method} {endpoint}: {resp.status}")
            body_text = resp.read().decode()
            print(f"Body: {body_text[:1000]}")
            return json.loads(body_text)
    except urllib.error.HTTPError as e:
        print(f"{method} {endpoint} failed: {e.code}")
        print(f"Body: {e.read().decode()[:1000]}")
        return None

if __name__ == "__main__":
    token = login()
    if token:
        print("Login OK")
        # First create an import
        file_path = r"C:\Users\asada\Desktop\coe_mixed_test_data_100plus\01_students_mixed.xlsx"
        
        # Upload file
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"\r\n'.encode()
        body += b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
        body += file_content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        
        req = urllib.request.Request(f"{API_BASE}/api/v1/imports", data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                import_id = result.get("import_id")
                print(f"Created import_id: {import_id}")
                
                # Now test validate endpoint
                print(f"\n--- Test Validate (POST /api/v1/imports/{import_id}/validate) ---")
                test_endpoint(token, f"/api/v1/imports/{import_id}/validate", "POST")
                
                # Test get import details
                print(f"\n--- Test Get Import (GET /api/v1/imports/{import_id}) ---")
                test_endpoint(token, f"/api/v1/imports/{import_id}", "GET")
                
        except urllib.error.HTTPError as e:
            print(f"Upload failed: {e.code}")
            print(f"Body: {e.read().decode()[:500]}")