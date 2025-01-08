from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.post("/webhook")
async def webhook(file: UploadFile = File(...)):
    try:
        print({"filename": file.filename, "content_type": file.content_type})
        return {"message": "Archivo procesado correctamente"}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    
@app.get("/webhook")
async def verify_webhook(request: Request, hub_mode: str = None, hub_challenge: str = None, hub_verify_token: str = None):
    # Aquí validas el `hub_verify_token` con el valor esperado
    expected_token = "EAAXRz1H2U84BOzvhWOslZAnVryCduZCQb8XWmk5tZAcxuOJKOiEwtH83maCUz8MMMZAnuDe4Y0y3kkdDoAycjl5SLWRVO5EvYKroSSDdziC0BbtSTDBt81FlQLGvWT6eMm0xGJZBAXHZAIKnBrOuvwnr4km0ekOuzTOOJxVlJZBICv6ygut1tRHz3rlnmvsQgBDKRjzn0ZCMzpsdqKlCVjy0ePko7IW2won7gOt4PditCAZDZD"
    
    if hub_verify_token == expected_token:
        if hub_mode == "subscribe":
            return PlainTextResponse(content=hub_challenge)
    else:
        return PlainTextResponse(content="Unauthorized", status_code=403)