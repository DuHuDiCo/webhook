from fastapi import FastAPI, File, UploadFile, HTTPException


app = FastAPI()

@app.post("/webhook")
async def webhook(file: UploadFile = File(...)):
    try:
        return {"message": "Archivo procesado correctamente"}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error interno: {str(e)}")