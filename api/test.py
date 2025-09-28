from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Test API working", "status": "success"}

@app.get("/test")
def test_endpoint():
    return {"test": "This is a test endpoint"}

# Export for Vercel
handler = app
