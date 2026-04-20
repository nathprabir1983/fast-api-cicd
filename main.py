# app/main.py

import os
import uvicorn
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.database import engine, Base, get_db
from fastapi.responses import FileResponse
from pdf2docx import Converter

Base.metadata.create_all(bind=engine)

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/convert/")
async def convert_pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    output_filename = file.filename.replace(".pdf", ".docx")
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Convert to DOCX
    try:
        converter = Converter(input_path)
        converter.convert(output_path, start=0, end=None)
        converter.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=output_filename)

@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)

@app.get("/items/", response_model=list[schemas.Item])
def read_items(db: Session = Depends(get_db)):
    return crud.get_items(db)

@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    updated = crud.update_item(db, item_id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}

#if __name__ == "__main__":
#    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
