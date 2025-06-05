import os
import face_recognition

class FaceAPI:
    def __init__(self, model_path):
        self.model_path = model_path
        self._load_models()

    def _load_models(self):
        """Load face-api.js models from the specified path."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model path {self.model_path} does not exist.")
        
        # Placeholder for loading models
        print(f"[INFO] Models loaded from {self.model_path}")

    def verify_face(self, stored_face_data, submitted_face_image):
        """Verify if the submitted face matches the stored face data."""
        try:
            # Decode the submitted face image
            print(f"[DEBUG] Processing submitted face image: {submitted_face_image}")
            submitted_face = face_recognition.load_image_file(submitted_face_image)
            face_encodings = face_recognition.face_encodings(submitted_face)
            if not face_encodings:
                print("[ERROR] No face detected in the submitted image.")
                return False
            submitted_face_encoding = face_encodings[0]

            # Compare with stored face data
            print(f"[DEBUG] Comparing face encodings...")
            results = face_recognition.compare_faces([stored_face_data], submitted_face_encoding)
            return results[0]
        except Exception as e:
            print(f"[ERROR] Face verification failed: {e}")
            return False
