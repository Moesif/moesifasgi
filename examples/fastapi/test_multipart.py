import requests

url = "http://127.0.0.1:8000/upload/"
file_path = "test_file.txt"

# Create a test file
with open(file_path, "w") as f:
    f.write("This is a test file.")

# Send the multipart request
with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "text/plain")}
    response = requests.post(url, files=files)

print("Response:", response.json())
