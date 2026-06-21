
import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImppZmtyeHF6ZmNqaWV4dmprcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE2OTczNzksImV4cCI6MjA5NzI3MzM3OX0.LSsjYIWW42YKnAGLt05hHV1ORwJFZHIY5VQf3w3N_kY"
secret = "zZVIfbxW+pPC4ILk+0djFUMBsqo6lEtEb6UxoEiH0npUZim+YEH43i7iI3NdhrlsVDxxYfXak6UDZV5VuoRtNw=="

try:
    print("Trying with raw secret string:")
    payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
    print("Success:", payload)
except Exception as e:
    print("Failed with raw secret:", e)

try:
    print("\nTrying with base64 decoded secret:")
    import base64

    payload = jwt.decode(
        token, base64.b64decode(secret), algorithms=["HS256"], options={"verify_aud": False}
    )
    print("Success:", payload)
except Exception as e:
    print("Failed with base64 decoded:", e)
