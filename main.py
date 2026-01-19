from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd
import os
import uuid
from pathlib import Path

app = FastAPI()

# Create folders if not present
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

@app.get("/")
def home():
    return HTMLResponse(open("index.html", encoding="utf-8").read())

@app.post("/clean")
async def clean_data(
    file: UploadFile = File(...),
    trim_spaces: bool = Form(False),
    remove_duplicates: bool = Form(False),
    remove_blank_rows: bool = Form(False)
):
    # -------------------------
    # Save uploaded file
    # -------------------------
    file_id = str(uuid.uuid4())
    input_path = Path("uploads") / f"{file_id}_{file.filename}"
    output_path = Path("outputs") / f"cleaned_{file.filename}"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    filename = file.filename.lower()

    # -------------------------
    # Read file safely
    # -------------------------
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(input_path)

        elif filename.endswith(".xlsx"):
            df = pd.read_excel(input_path, engine="openpyxl")

        elif filename.endswith(".xls"):
            # Legacy Excel handling
            df = pd.read_excel(input_path, engine="xlrd")

        else:
            return HTMLResponse(
                "❌ Unsupported file type. Please upload CSV, XLS, or XLSX.",
                status_code=400
            )

    except Exception as e:
        return HTMLResponse(
            f"❌ Error reading file: {str(e)}",
            status_code=500
        )

    # -------------------------
    # Cleaning rules
    # -------------------------
    if remove_blank_rows:
        df = df.dropna(how="all")

    if trim_spaces:
        df = df.applymap(
    lambda x: " ".join(x.split()) if isinstance(x, str) else x
)


    if remove_duplicates:
        df = df.drop_duplicates()

    # -------------------------
    # Save cleaned file
    # -------------------------
    try:
        if filename.endswith(".csv"):
            df.to_csv(output_path, index=False)
        else:
            df.to_excel(output_path, index=False)
    except Exception as e:
        return HTMLResponse(
            f"❌ Error saving cleaned file: {str(e)}",
            status_code=500
        )

    return FileResponse(
        path=output_path,
        filename=f"cleaned_{file.filename}",
        media_type="application/octet-stream"
    )
