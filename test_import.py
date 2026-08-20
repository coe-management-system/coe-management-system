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

def upload_file(token, file_path, import_type=None):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(file_path, "rb") as f:
        file_content = f.read()

    body = b""
    # Add import_type field if provided
    if import_type:
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="import_type"\r\n\r\n'.encode()
        body += f"{import_type}\r\n".encode()

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
            print(f"Upload response: {resp.status}")
            print(f"Body: {resp.read().decode()[:500]}")
    except urllib.error.HTTPError as e:
        print(f"Upload failed: {e.code}")
        print(f"Body: {e.read().decode()[:500]}")

if __name__ == "__main__":
    token = login()
    if token:
        print("Login OK")
        file_path = r"C:\Users\asada\Desktop\coe_mixed_test_data_100plus\01_students_mixed.xlsx"
        print("\n--- Test 1: Upload without import_type ---")
        upload_file(token, file_path)
        print("\n--- Test 2: Upload with import_type=student ---")
        upload_file(token, file_path, import_type="student")