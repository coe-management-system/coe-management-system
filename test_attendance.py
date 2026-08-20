import urllib.request
import json
import os

API = "http://127.0.0.1:8000"

# Login
login_data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(f"{API}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["access_token"]

def upload_and_process(file_path, import_type=None):
    boundary = "----B"
    with open(file_path, "rb") as f:
        fc = f.read()
    
    body = b""
    if import_type:
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="import_type"\r\n\r\n'.encode()
        body += f"{import_type}\r\n".encode()
    
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"\r\n'.encode()
    body += b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    body += fc + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
    resp = json.loads(urllib.request.urlopen(urllib.request.Request(f"{API}/api/v1/imports", data=body, headers=headers, method="POST")).read())
    import_id = resp["import_id"]
    
    # Validate
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    val = json.loads(urllib.request.urlopen(urllib.request.Request(f"{API}/api/v1/imports/{import_id}/validate", method="POST", headers=h)).read())
    
    # Commit
    commit = json.loads(urllib.request.urlopen(urllib.request.Request(f"{API}/api/v1/imports/{import_id}/commit", method="POST", headers=h)).read())
    
    return val["summary"], commit

print("=== 03_attendance_mixed.xlsx ===")
try:
    val, commit = upload_and_process(r"C:\Users\asada\Desktop\coe_mixed_test_data_100plus\03_attendance_mixed.xlsx")
    print(f"Validate: {val}")
    print(f"Commit: imported={commit['imported_count']}")
except Exception as e:
    print(f"Error: {e}")