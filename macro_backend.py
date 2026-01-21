from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import win32com.client as win32
import tempfile
import os
import shutil
import pythoncom

app = FastAPI()


@app.post("/apply-macro")
async def apply_macro(
    excel_file: UploadFile = File(...),
    macro_file: UploadFile = File(...)
):
    pythoncom.CoInitialize()

    temp_dir = tempfile.mkdtemp()

    input_excel = os.path.join(temp_dir, excel_file.filename)
    macro_path = os.path.join(temp_dir, macro_file.filename)
    output_excel = os.path.join(temp_dir, "output.xlsx")

    # Save uploaded files
    with open(input_excel, "wb") as f:
        shutil.copyfileobj(excel_file.file, f)

    with open(macro_path, "wb") as f:
        shutil.copyfileobj(macro_file.file, f)

    excel = None
    try:
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        wb = excel.Workbooks.Open(input_excel)

        # Inject macro
        wb.VBProject.VBComponents.Import(macro_path)

        # ⚠️ Change macro name if needed
        excel.Run("Main")

        wb.SaveAs(output_excel, FileFormat=51)  # xlsx
        wb.Close(False)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

    finally:
        if excel:
            excel.Quit()
        pythoncom.CoUninitialize()

    return FileResponse(
        output_excel,
        filename="macro_applied.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
