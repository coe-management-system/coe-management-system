import urllib.request
import json
import os

API = "http://127.0.0.1:8000"

# Login
login_data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(f"{API}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["access_token"]

# Create fresh import
boundary = "----B"
file_path = r"C:\Users\asada\Desktop\coe_mixed_test_data_100plus\01_students_mixed.xlsx"
with open(file_path, "rb") as f:
    fc = f.read()

body = b""
body += f"--{boundary}\r\n".encode()
body += f'Content-Disposition: form-data; name="file"; filename="test.xlsx"\r\n'.encode()
body += b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
body += fc + b"\r\n"
body += f"--{boundary}--\r\n".encode()

headers = {"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
resp = json.loads(urllib.request.urlopen(urllib.request.Request(f"{API}/api/v1/imports", data=body, headers=headers, method="POST")).read())
import_id = resp["import_id"]
print(f"Created import: {import_id}")

# Validate
h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
val = json.loads(urllib.request.urlopen(urllib.request.Request(f"{API}/api/v1/imports/{import_id}/validate", method="POST", headers=h)).read())
print("Summary:", val["summary"])