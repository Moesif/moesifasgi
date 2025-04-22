import requests

def test_file_upload():
    url = "http://127.0.0.1:8000/upload/"
    file_path = "test_file.txt"

    # Create a test file
    with open(file_path, "w") as f:
        f.write("This is a test file.")

    # Send the multipart request
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "text/plain")}
        response = requests.post(url, files=files)

    print("File Upload Response:", response.json())

def test_normal_form():
    url = "http://127.0.0.1:8000/submit-form/"

    # Normal form data
    form_data = {
        "username": "testuser",
        "email": "test@example.com",
        "message": "Hello, this is a test message!"
    }

    # Send the form data request
    response = requests.post(url, data=form_data)
    print("Form Submit Response:", response.json())

if __name__ == "__main__":
    # Run both tests
    print("Testing file upload...")
    test_file_upload()

    print("\nTesting normal form submission...")
    test_normal_form()
