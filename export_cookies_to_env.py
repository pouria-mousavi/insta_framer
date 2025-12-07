import base64
import os

def export_cookies():
    cookie_file = "cookies.txt"
    if not os.path.exists(cookie_file):
        print(f"Error: {cookie_file} not found. Please run the bot locally once to generate it (or ensure you are logged in).")
        return

    with open(cookie_file, 'rb') as f:
        cookie_data = f.read()
    
    b64_cookies = base64.b64encode(cookie_data).decode('utf-8')
    
    print("\n✅ COOKIES EXPORTED SUCCESSFULLY!")
    print("Copy the following long string and add it as an Environment Variable in Render:")
    print("Key: COOKIES_B64")
    print("Value:")
    print("-" * 20)
    print(b64_cookies)
    print("-" * 20)

if __name__ == "__main__":
    export_cookies()
