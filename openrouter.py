
import os
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


import requests
import json
import data_url
import base64
import time
import os
from session import Session


def encode_bytestream_to_base64(bytes):
    return base64.b64encode(bytes).decode('utf-8')
    
def make_dataurl(base64_image):
	data_url = f"data:image/jpeg;base64,{base64_image}"
	return { "type": "image_url",
			"image_url": { "url": data_url	}
            }


def openrouter_request_gemini_imageedit(prompt, images, n=2):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "Telegram imageedit bot"
        
    }
    
    content = [ {  "type": "text",  "text": prompt    } ]
    for im in images:
        content.append( make_dataurl(encode_bytestream_to_base64(im)) )

    payload = {
        "model": "google/gemini-2.5-flash-image-preview",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        #"modalities": ["image"],
        "modalities": ["image", "text"],
        #"provider": { 'only': [ 'Google' ] }
        #"provider": { 'only': [ "Google AI Studio" ] }
    }

    sess = Session("sess_payload")
    sess.append( sess.makeFilename("payload","txt") , json.dumps( payload , indent=2 , ensure_ascii=False ))

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    sess.append( sess.makeFilename("reply","txt") , json.dumps( result , indent=2, ensure_ascii=False))
    
    if result.get("choices"):
        message = result["choices"][0]["message"]
        if ("images" not in message) and ("content" in message) and len( message.get("content") )>0 and n>0:
            # google bug , retrying
            print("retrying ... (openrouter)")
            return openrouter_request_gemini_imageedit(prompt, images, n-1)
            
        if message.get("images"):
            for image in message["images"]:
                image_url = image["image_url"]["url"]  # Base64 data URL
                print(f"Generated image: {image_url[:50]}...")
                return data_url_image_to_bytes(image_url)
    return None


def data_url_image_to_bytes(image_url):

    # https://pypi.org/project/data-url/
    url = data_url.DataURL.from_url(image_url)
    
    #print(url.mime_type, url.is_base64_encoded, url.data)

    # Get the mime type and extract extension
    mime_type = url.mime_type
    if mime_type == 'image/jpeg':
        extension = 'jpg'
    elif mime_type == 'image/png':
        extension = 'png'
    elif mime_type == 'image/gif':
        extension = 'gif'
    elif mime_type == 'image/webp':
        extension = 'webp'
    else:
        extension = 'jpg'  # default fallback

    # Get unix timestamp
    unix_time = int(time.time())

    # Create incoming directory if it doesn't exist
    os.makedirs('incoming', exist_ok=True)

    # Save the file
    filename = f"incoming/{unix_time}.{extension}"
    with open(filename, 'wb') as f:
        f.write(url.data)
    print(f"Image saved as: {filename}")
    
    return url.data
