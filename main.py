from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import pandas as pd
import os
import uuid
import re

app = FastAPI()

# Create folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

@app.get("/")
def health():
    return {"status": "Data Cleaner API is running"}

@app.post("/clean")
async def clean_data(
    file: UploadFile = File(...),
    trim_spaces: bool = Form(False),
    remove_duplicates: bool = Form(False),
    remove_blank_rows: bool = Form(False)
):
    file_id = str(uuid.uuid4())
    input_path = f"uploads/{file_id}_{file.filename}"
    output_path = f"outputs/cleaned_{file_id}_{file.filename}"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Read file
    if file.filename.lower().endswith(".csv"):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path, engine="openpyxl")

    # Preview BEFORE
    preview_before = df.head(10).fillna("").to_dict(orient="records")

    # Cleaning logic
    if remove_blank_rows:
        df = df.dropna(how="all")

    if trim_spaces:
        df = df.applymap(
            lambda x: re.sub(r"\s+", " ", x).strip() if isinstance(x, str) else x
        )

    if remove_duplicates:
        df = df.drop_duplicates()

    # Preview AFTER
    preview_after = df.head(10).fillna("").to_dict(orient="records")

    # Save file
    if file.filename.lower().endswith(".csv"):
        df.to_csv(output_path, index=False)
    else:
        df.to_excel(output_path, index=False)

    return {
        "preview_before": preview_before,
        "preview_after": preview_after,
        "download_url": f"/download/{os.path.basename(output_path)}"
    }

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = f"outputs/{filename}"
    return FileResponse(file_path, filename=filename)
