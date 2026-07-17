import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
from utils.helper import allowed_file, generate_unique_filename, get_current_timestamp
from predict import predict_disease
from explain import generate_disease_explanation
from translate import translate_explanation
from speech import generate_speech

app = FastAPI(title="Plant Disease Detection & Health Assistant API")

# Mount Static Folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/output_audio", StaticFiles(directory="output_audio"), name="output_audio")

# Set up templates folder
templates = Jinja2Templates(directory="templates")

# ==========================================
# Pydantic Schemas for Requests
# ==========================================
class ExplanationRequest(BaseModel):
    disease_name: str

class TranslationRequest(BaseModel):
    explanation: dict
    target_lang: str

class SpeechRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    message: str
    history: list
    disease_name: str

# Dummy History database response
DUMMY_HISTORY = [
    {
        "id": "hist_1",
        "image_url": "/static/images/history_placeholder_1.jpg",
        "disease": "Potato - Late Blight",
        "confidence": 0.89,
        "date": "2026-07-09",
        "time": "14:23:10"
    },
    {
        "id": "hist_2",
        "image_url": "/static/images/history_placeholder_2.jpg",
        "disease": "Tomato - Healthy",
        "confidence": 0.98,
        "date": "2026-07-08",
        "time": "09:12:44"
    },
    {
        "id": "hist_3",
        "image_url": "/static/images/history_placeholder_3.jpg",
        "disease": "Corn (Maize) - Common Rust",
        "confidence": 0.91,
        "date": "2026-07-05",
        "time": "16:45:19"
    }
]

# ==========================================
# Routes
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the Home Page (index.html).
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "maintenance_mode": config.MAINTENANCE_MODE, 
            "maintenance_time": config.MAINTENANCE_TIME
        }
    )

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Upload a leaf image and get the predicted disease.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Allowed formats: {config.ALLOWED_EXTENSIONS}"
        )
        
    try:
        # Generate unique name and save the file
        unique_name = generate_unique_filename(file.filename)
        save_path = os.path.join(config.UPLOAD_FOLDER, unique_name)
        
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Run mock / real prediction
        prediction_result = predict_disease(save_path, original_filename=file.filename)
        
        # Add relative URL path for the frontend to preview
        prediction_result["image_url"] = f"/uploads/{unique_name}"
        prediction_result["timestamp"] = get_current_timestamp()
        
        return prediction_result
        
    except FileNotFoundError as fnf_err:
        raise HTTPException(status_code=404, detail=str(fnf_err))
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/explain")
async def explain(request: ExplanationRequest):
    """
    Get detailed agricultural advice & instructions for the predicted disease.
    """
    try:
        explanation = generate_disease_explanation(request.disease_name)
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

@app.post("/translate")
async def translate(request: TranslationRequest):
    """
    Translate the agricultural cards to the target language.
    """
    try:
        translated = translate_explanation(request.explanation, request.target_lang)
        return translated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@app.post("/speech")
async def speech(request: SpeechRequest):
    """
    Generate a speech audio file from the provided text.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text parameter cannot be empty")
            
        audio_filename = generate_speech(request.text)
        audio_url = f"/output_audio/{audio_filename}"
        
        return {"audio_url": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech generation error: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Handle follow-up questions from the farmer via Grok Chat.
    """
    try:
        from explain import chat_with_grok
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        response_text = chat_with_grok(request.message, request.history, request.disease_name)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/history")
async def get_history():
    """
    Retrieve previous prediction history.
    Currently returns dummy database records.
    """
    # In the future: query your SQLite database here
    # select * from history order by timestamp desc
    return DUMMY_HISTORY

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)
