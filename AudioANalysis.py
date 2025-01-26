import yaml
import boto3
import tempfile
import os
import requests
from collections import defaultdict
from gtts import gTTS
import pyttsx3

# --------------------------
# CONFIGURATION SETTINGS
# --------------------------
OPENROUTER_API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct"
AWS_REGION = "us-east-1"  # Replace with your AWS region

# Initialize AWS Polly
polly_client = boto3.client("polly", region_name=AWS_REGION)

# --------------------------
# DATA PROCESSING FUNCTIONS
# --------------------------
def analyze_match(file_path):
    """Main function to process match data and generate analysis"""
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        
        stats = process_stats(data)
        analysis = get_ai_analysis(data)
        return stats, analysis
    except Exception as e:
        print(f"Error analyzing match: {str(e)}")
        return None, "Analysis unavailable due to an error."

def process_stats(data):
    """Process ball-by-ball data into structured statistics"""
    stats = {
        'batting': defaultdict(lambda: {'runs': 0, 'balls': 0, '4s': 0, '6s': 0}),
        'bowling': defaultdict(lambda: {'runs': 0, 'wickets': 0, 'balls': 0}),
        'team_scores': defaultdict(int),
        'info': data.get('info', {})
    }

    for innings in data.get('innings', []):
        inns_name, inns_data = next(iter(innings.items()))
        team = inns_data['team']
        for delivery in inns_data['deliveries']:
            ball_data = next(iter(delivery.values()))
            update_batting_stats(stats['batting'], ball_data)
            update_bowling_stats(stats['bowling'], ball_data)
            stats['team_scores'][team] += ball_data['runs']['total']

    calculate_derived_metrics(stats)
    return stats

def update_batting_stats(batting_stats, ball_data):
    batsman = ball_data['batsman']
    runs = ball_data['runs']['batsman']
    batting_stats[batsman]['runs'] += runs
    batting_stats[batsman]['balls'] += 1
    if runs == 4:
        batting_stats[batsman]['4s'] += 1
    if runs == 6:
        batting_stats[batsman]['6s'] += 1

def update_bowling_stats(bowling_stats, ball_data):
    bowler = ball_data['bowler']
    bowling_stats[bowler]['runs'] += ball_data['runs']['total']
    bowling_stats[bowler]['balls'] += 1
    if "wicket" in ball_data:
        bowling_stats[bowler]['wickets'] += 1

def calculate_derived_metrics(stats):
    for batsman, data in stats['batting'].items():
        data['strike_rate'] = round((data['runs'] / data['balls']) * 100, 2) if data['balls'] > 0 else 0
    for bowler, data in stats['bowling'].items():
        overs = data['balls'] / 6
        data['economy'] = round(data['runs'] / overs, 2) if overs > 0 else 0
        data['overs'] = round(overs, 1)

# --------------------------
# AI ANALYSIS FUNCTION
# --------------------------
def get_ai_analysis(data):
    """Generate analysis using OpenRouter API"""
    match_info = {
        "city": data["info"].get("city", "Unknown"),
        "teams": data["info"].get("teams", []),
        "winner": data["info"].get("outcome", {}).get("winner", "Unknown"),
    }

    prompt = f"""Analyze this cricket match data:
    Location: {match_info["city"]}
    Teams: {match_info["teams"]}
    Winner: {match_info["winner"]}

    Provide detailed analysis including:
    1. Key performances with statistics
    2. Match turning points
    3. Recommendations"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1500,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API Error: {e}")
        return "Analysis unavailable due to API error."

# --------------------------
# AUDIO OUTPUT FUNCTION
# --------------------------
def create_audio_output(text, output_file, use_offline=False):
    """Generate audio from text using either gTTS or pyttsx3"""
    try:
        if not use_offline:
            # Online Google TTS
            tts = gTTS(text=text, lang='en')
            tts.save(output_file)
        else:
            # Offline pyttsx3
            engine = pyttsx3.init()
            engine.save_to_file(text, output_file)
            engine.runAndWait()
        return True
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        print("Trying fallback method...")
        try:
            # Fallback to other method
            if use_offline:
                tts = gTTS(text=text, lang='en')
                tts.save(output_file)
            else:
                engine = pyttsx3.init()
                engine.save_to_file(text, output_file)
                engine.runAndWait()
            return True
        except Exception as e:
            print(f"Fallback failed: {str(e)}")
            return False

# --------------------------
# MAIN EXECUTION
# --------------------------
if __name__ == "__main__":
    file_path = r"C:\Users\DELL\Downloads\all\1416490.yaml"  # Replace with your YAML file path
    stats, analysis = analyze_match(file_path)

    if stats and analysis:
        audio_output_file = "match_analysis.mp3"
        success = create_audio_output(analysis, audio_output_file, use_offline=False)
        if success:
            print(f"Analysis audio generated successfully at: {os.path.abspath(audio_output_file)}")
        else:
            print("Failed to generate audio.")
    else:
        print("Failed to generate analysis.")
