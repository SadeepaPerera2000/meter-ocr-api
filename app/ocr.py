# app/ocr.py


import os
import time
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv


# Load env variables from .env file
load_dotenv()


GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)


model = genai.GenerativeModel('gemini-2.5-flash')


# Prompt to extract meter reading
PROMPT = """ Extract the numerical meter reading from the main rectangular display of this electricity meter. The display is typically in the top half of the image. The meter reading is expected to be a number between 5 and 8 digits long. Focus on the larger digits representing the primary meter reading and ignore any smaller digits (e.g., those after a decimal point). If the meter reading cannot be confidently identified or extracted, respond with "Unreadable". Provide only the extracted numerical reading or "Unreadable", with no other text. """


# API rate limit parameters (Gemini 2.5 Flash)
MAX_REQUESTS_PER_MINUTE = 10


class RateLimiter:
   def __init__(self, max_requests_per_minute):
       self.max_requests = max_requests_per_minute
       self.requests = 0
       self.start_time = time.time()


   def wait_if_needed(self):
       if self.requests >= self.max_requests:
           elapsed = time.time() - self.start_time
           if elapsed < 60:
               wait_time = 60 - elapsed
               print(f"Rate limit reached. Sleeping for {wait_time:.2f} seconds...")
               time.sleep(wait_time)
           self.requests = 0
           self.start_time = time.time()
       self.requests += 1




rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE)




def extract_meter_reading(image_path: str) -> str:
   """
   Extracts the meter reading from the given image using Gemini 2.5 Flash model.
   Returns the extracted reading as a string, or 'Unreadable' on failure.
   """
   try:
       rate_limiter.wait_if_needed()
       img = Image.open(image_path)
       response = model.generate_content([PROMPT, img])
       reading = response.text.strip()
       return reading
   except Exception as e:
       print(f"Error processing {image_path}: {e}")
       return "Unreadable"




if __name__ == "__main__":
   # Example test (run directly to test)
   test_dir = "path_to_some_test_images"
   for img_file in os.listdir(test_dir):
       img_path = os.path.join(test_dir, img_file)
       if os.path.isfile(img_path):
           result = extract_meter_reading(img_path)
           print(f"{img_file}: {result}")