import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import json

# API Configuration
OPENROUTER_API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct"

def scrape_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            return ' '.join([p.get_text().strip() for p in paragraphs])
        else:
            print(f"Failed to retrieve webpage. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error scraping website: {e}")
        return None

def process_with_openrouter(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:5000",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Summarize the following content:"},
            {"role": "user", "content": text}
        ]
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error processing with AI: {e}")
        return None

def text_to_speech(text, output_file):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(output_file)
        return True
    except Exception as e:
        print(f"Error creating audio: {e}")
        return False

if __name__ == "__main__":
    url = "https://www.aparnaconstructions.com/project/apartments/aparna-zenon/"
    output_audio = "summary.mp3"
    
    # Execute pipeline
    content = scrape_website(url)
    if content:
        summary = process_with_openrouter(content)
        if summary:
            if text_to_speech(summary, output_audio):
                print(f"Summary saved as audio to {output_audio}")
                print("\nText Summary:")
                print(summary)
