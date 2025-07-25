from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # <-- Import CORS middleware
import os
import logging
import json
from dotenv import load_dotenv
import time  # ⏱️ For rate-limiting sleep
import base64

from app.ocr import extract_meter_reading
from app.drive_utils import list_files_in_folder, download_file

# Load environment variables
load_dotenv()

# Create LOCAL_IMAGE_DIR if not exists (important for Cloud Run)
save_dir = os.getenv("LOCAL_IMAGE_DIR")
if save_dir:
    os.makedirs(save_dir, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()

# === CORS Setup: Allow all origins ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
def read_root():
    return {"message": "Hello, Meter Reader!"}


@app.get("/ocr/single/{image_name}")
def read_meter(image_name: str):
    image_dir = os.getenv("LOCAL_IMAGE_DIR")
    image_path = os.path.join(image_dir, image_name)

    logging.info(f"Checking image path: {image_path}")

    if not os.path.exists(image_path):
        logging.warning(f"Image not found: {image_path}")
        raise HTTPException(status_code=404, detail="Image not found.")

    reading = extract_meter_reading(image_path)
    logging.info(f"Reading extracted from {image_name}: {reading}")

    return {
        "image": image_name,
        "reading": reading,
        "status": "OK" if reading != "Unreadable" else "Failed"
    }


@app.get("/test-download")
def test_download_images():
    TEST_FOLDER_ID = "1cu29xrTse-wm79_xHK6ApqyZVn_DPa7K"
    try:
        logging.info("Listing files in Google Drive folder...")
        files = list_files_in_folder(TEST_FOLDER_ID)

        if not files:
            logging.warning("No files found in the Drive folder.")
            return {"message": "No files found in the Drive folder."}

        save_dir = os.getenv("LOCAL_IMAGE_DIR")
        logging.info(f"Saving images to: {save_dir}")
        os.makedirs(save_dir, exist_ok=True)

        downloaded_files = []
        for file in files:
            logging.info(f"Downloading file: {file['name']}")
            file_path = download_file(file['id'], file['name'], save_dir)
            logging.info(f"Downloaded to: {file_path}")
            downloaded_files.append(os.path.basename(file_path))

        return {"downloaded_files": downloaded_files}
    except Exception as e:
        logging.error(f"Exception during download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/batch-process")
def extract_batch_meter_readings():
    save_dir = os.getenv("LOCAL_IMAGE_DIR")
    logging.info(f"LOCAL_IMAGE_DIR: {save_dir}")

    if not save_dir or not os.path.exists(save_dir):
        logging.error("LOCAL_IMAGE_DIR does not exist or is not set.")
        raise HTTPException(status_code=500, detail="Local image directory is not set or does not exist.")

    all_files = os.listdir(save_dir)
    logging.info(f"All files in directory: {all_files}")

    image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    logging.info(f"Image files to process: {image_files}")

    if not image_files:
        logging.warning("No image files found to process.")
        raise HTTPException(status_code=404, detail="No images found in local directory.")

    results = []
    for image_file in image_files:
        image_path = os.path.join(save_dir, image_file)
        logging.info(f"Checking existence of: {image_path}")

        if not os.path.exists(image_path):
            logging.warning(f"Image not found: {image_path}")
            results.append({
                "image": image_file,
                "reading": None,
                "status": "Image not found"
            })
            continue

        reading = extract_meter_reading(image_path)
        logging.info(f"Extracted from {image_file}: {reading}")

        results.append({
            "image": image_file,
            "reading": reading,
            "status": "OK" if reading and reading != "Unreadable" else "Failed"
        })

    logging.info(f"Final Results: {results}")
    return {"results": results}


@app.get("/ocr/ui-data")
def get_ui_data():
    save_dir = os.getenv("LOCAL_IMAGE_DIR")
    if not save_dir or not os.path.exists(save_dir):
        raise HTTPException(status_code=500, detail="Local image directory is not set or does not exist.")

    all_files = os.listdir(save_dir)
    image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        raise HTTPException(status_code=404, detail="No images found in local directory.")

    fixed_time = "2025-07-24 00:00:00"
    previous_status = ["OK", "Failed"]

    response = []

    for image_file in image_files:
        image_path = os.path.join(save_dir, image_file)

        if not os.path.exists(image_path):
            continue

        # ⏱️ Sleep to respect rate limits
        time.sleep(8)

        # Extract reading
        reading = extract_meter_reading(image_path)
        status = "OK" if reading and reading != "Unreadable" else "Failed"

        # Convert image to base64
        with open(image_path, "rb") as image_file_data:
            encoded_image = base64.b64encode(image_file_data.read()).decode("utf-8")

        response.append({
            "image_name": image_file,
            "reading": reading,
            "status": status,
            "time": fixed_time,
            "previous_status": previous_status,
            "image_base64": encoded_image
        })

    return {"data": response}


@app.get("/ocr/demo-readings")
def get_demo_readings():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "UI_Response", "ui_response.json")
        if not os.path.exists(file_path):
            logging.error("Demo UI response file not found.")
            raise HTTPException(status_code=404, detail="Demo UI response file not found.")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)

    except Exception as e:
        logging.error(f"Error reading demo UI file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")