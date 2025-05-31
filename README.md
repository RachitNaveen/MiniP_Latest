# SecureChatApp

A secure real-time chat application built with Flask, Socket.IO, and SQLite.
Supports user registration with face verification, login, real-time messaging, and more.

---

## 🚀 Features

- User registration with face data capture & login
- Face verification during login (configurable)
- Password hashing for secure storage
- Real-time public/private messaging with Socket.IO
- Online user list
- SQLite backend (local database)
- Docker support for easy setup and deployment

---

## 📦 Requirements

**For Local Development:**
- Python 3.x (e.g., 3.9+)
- Virtualenv (recommended)
- `pip` (Python package installer)
- `face-api.js` models (see setup instructions)

**For Docker Deployment:**
- Docker Desktop

---

## ⚙️ Setup Instructions

### Method 1: Local Setup (using Python Virtual Environment)

1.  **Clone the repository**
    ```bash
    git clone https://github.com/RachitNaveen/securechatapp.git # Or your repository URL
    cd securechatapp # Or your project directory name (minip_latest)
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you encounter issues with `face_recognition` or `dlib` installation, ensure you have `cmake` installed. On macOS: `brew install cmake`.*
    *If `pkg_resources` is not found during `face_recognition_models` installation, run: `pip install --upgrade setuptools` then retry step 3.*

4.  **Download `face-api.js` models:**
    The application uses `face-api.js` for client-side face detection during registration.
    - Download the model weights from: [https://github.com/justadudewhohacks/face-api.js/tree/master/weights](https://github.com/justadudewhohacks/face-api.js/tree/master/weights)
    - Create a directory `app/static/face-api-models`.
    - Place the downloaded `.weights` files into this `app/static/face-api-models/` directory.

5.  **Initialize the database:**
    The application will create the `instance` folder and `chat.db` file automatically when you first run it, thanks to `db.create_all()` in `run.py`.
    If you need to create the `instance` directory manually beforehand:
    ```bash
    mkdir instance
    ```
    Alternatively, you can run the `init_db.py` script once:
    ```bash
    python init_db.py
    ```

6.  **Run the application:**
    ```bash
    python run.py
    ```
    The application should be available at `http://127.0.0.1:5000`.

### Method 2: Docker Setup

This is the recommended method for easy setup and consistency across team members.

1.  **Ensure Docker Desktop is running.**

2.  **Clone the repository** (if you haven't already):
    ```bash
    git clone https://github.com/RachitNaveen/securechatapp.git # Or your repository URL
    cd securechatapp # Or your project directory name (minip_latest)
    ```

3.  **Download `face-api.js` models (Required for image build):**
    Ensure the `face-api.js` model weights are present in `app/static/face-api-models/` as described in Step 4 of the Local Setup. These files need to be present *before* building the Docker image as they are copied into the image.

4.  **Build the Docker image:**
    From the project root directory (where the `Dockerfile` is located):
    ```bash
    docker build -t minip-app .
    ```
    (You can replace `minip-app` with your preferred image name).

5.  **Run the Docker container:**
    ```bash
    docker run -p 5000:5000 -v "$(pwd)/instance":/app/instance --name minip-container minip-app
    ```
    - `-p 5000:5000`: Maps port 5000 on your host to port 5000 in the container.
    - `-v "$(pwd)/instance":/app/instance`: Mounts the local `instance` directory (for the SQLite database) into the container, ensuring data persistence.
    - `--name minip-container`: Assigns a name to the running container.

    The application should be available at `http://localhost:5000`.

---

## 📄 Notes

- The `.gitignore` file is configured to exclude the `venv/` directory, `__pycache__` folders, and the `instance/chat.db` database file (as it's managed via Docker volumes or created locally).
- Configuration settings (like `SECRET_KEY`, database URI, face verification thresholds) are in `config.py`. For production, `SECRET_KEY` and database credentials should be set via environment variables.
- The `FACE_VERIFICATION_REQUIRED` setting in `config.py` can be toggled to enable/disable mandatory face verification.

# miniproject
# miniproject
# miniproject
# minip_latest
