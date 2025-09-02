
import datetime
import os, os.path
import requests
from urllib.parse import urlparse


class Session:
    def __init__(self, mainfolder):
        
        
        # session start time, datetime in format YYYYmmdd-hhmmss-milliseconds
        self.session_start = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        
        self.mainFolder = mainfolder
        
        # concatenate self.mainFolder and self.session_start with os.path
        self.sessionFolder = os.path.join(self.mainFolder, self.session_start)
        
        # ensure that self.sessionFolder exists. create if needed
        os.makedirs(self.sessionFolder, exist_ok=True)
        
        self.filenamePrefixes = {}
        
    def makeFilename(self, prefix,ext):
        
        if prefix not in self.filenamePrefixes:
            self.filenamePrefixes[prefix] = 0
        self.filenamePrefixes[prefix] += 1
        idx = self.filenamePrefixes[prefix]
        
        filename = os.path.join(self.sessionFolder, f"{prefix}{idx:02}.{ext}")
        
        return filename
    
    def append(self,filename, text):
        with open(filename, "a", encoding='utf-8') as f:
            f.write(text)
            f.write("\n\n")
            
    def write(self,filename, binary_data):
        with open(filename, "wb", encoding='utf-8') as f:
            f.write(binary_data)
            
            
    def download_image(self,image_url, prefix = "input"):

        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()

        # Get extension from URL path
        parsed_url = urlparse(image_url)
        extension = os.path.splitext(parsed_url.path)[1]

        # If no extension in URL, try to detect from content-type
        if not extension:
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                extension = '.jpg'
            elif 'png' in content_type:
                extension = '.png'
            elif 'gif' in content_type:
                extension = '.gif'
            elif 'webp' in content_type:
                extension = '.webp'
            else:
                extension = '.jpg'  # default fallback

        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)

        # Save the file
        filename = self.makeFilename(prefix,extension)
        self.write(filename, response.content)
