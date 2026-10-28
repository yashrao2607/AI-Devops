import os

def start_server():
    debug_mode = os.getenv("DEBUG", "False") == "True"
    print(f"Starting server in debug mode: {debug_mode}")

if __name__ == "__main__":
    start_server()
