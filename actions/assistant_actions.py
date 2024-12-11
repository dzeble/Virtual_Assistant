#imports
import speech_recognition as sr
import pyttsx3
import webbrowser
import urllib.parse
# import datetime
import requests
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pickle



#news api key
NEWS_API_KEY = "2a0be3767ca24e52b8a51b04bc3cf338"
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

#function for the assistant to take notes
def save_note(note_content):
    try:
        # Create notes directory if it doesn't exist
        notes_dir = "notes"
        if not os.path.exists(notes_dir):
            os.makedirs(notes_dir)
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_{timestamp}.txt"
        filepath = os.path.join(notes_dir, filename)
        
        # Save the note with timestamp
        with open(filepath, "w") as f:
            f.write(f"Note created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(note_content)
        
        return f"Note saved successfully as {filename}"
    except Exception as e:
        print(f"Error saving note: {e}")
        return "Sorry, I couldn't save your note."


#function for the assistant to get news
def get_news(category=None, query=None, country='us'):
    try:
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "country": country
        }
        
        if category:
            params["category"] = category
        if query:
            params["q"] = query
            
        response = requests.get(base_url, params=params)
        news_data = response.json()
        
        if news_data["status"] == "ok" and news_data["articles"]:
            articles = news_data["articles"][:5]  # Get top 5 articles
            news_summary = "Here are the top headlines:\n\n"
            
            for i, article in enumerate(articles, 1):
                news_summary += f"{i}. {article['title']}\n"
                if article['description']:
                    news_summary += f"   {article['description']}\n\n"
                    
            return news_summary
        else:
            return "Sorry, I couldn't fetch any news at the moment."
            
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "Sorry, I couldn't fetch the news right now."

#function for the assistant to get wikipedia information
def get_wikipedia_summary(query):
    try:
        # Remove 'wikipedia' from the query if present
        search_term = query.replace('wikipedia', '').strip()
        
        # First, search for the page
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(search_term)}&format=json"
        search_response = requests.get(search_url)
        search_data = search_response.json()
        
        if not search_data['query']['search']:
            return "Sorry, I couldn't find any information about that."
            
        # Get the first result's page ID
        page_id = search_data['query']['search'][0]['pageid']
        
        # Get the page content
        content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&pageids={page_id}&format=json"
        content_response = requests.get(content_url)
        content_data = content_response.json()
        
        # Extract the summary
        page_content = content_data['query']['pages'][str(page_id)]['extract']
        # Get first two sentences or first 250 characters, whichever is shorter
        summary = ' '.join(page_content.split('. ')[:2]) + '.'
        if len(summary) > 250:
            summary = page_content[:250] + '...'
        
        return summary

    except Exception as e:
        print(f"Error fetching Wikipedia information: {e}")
        return "Sorry, I couldn't fetch that information."


def get_google_calendar_service():
    """Get or refresh Google Calendar credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def create_calendar_reminder(text, reminder_time):
    """Create a Google Calendar event for the reminder."""
    try:
        service = get_google_calendar_service()
        
        # Create the event
        event = {
            'summary': f'Reminder: {text}',
            'description': f'Reminder set by Virtual Assistant: {text}',
            'start': {
                'dateTime': reminder_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (reminder_time + timedelta(minutes=30)).isoformat(),
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 0},
                    {'method': 'email', 'minutes': 5},
                ],
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return True, f"Reminder set in Google Calendar for {reminder_time.strftime('%Y-%m-%d %H:%M')}"
    except Exception as e:
        return False, f"Error setting reminder in Google Calendar: {e}"

def parse_time(time_input):
    """Parse time input in various formats."""
    try:
        time_input = time_input.lower().strip()
        current_time = datetime.now()
        reminder_time = current_time

        # Handle "tomorrow"
        if 'tomorrow' in time_input:
            reminder_time = current_time + timedelta(days=1)
            time_input = time_input.replace('tomorrow', '').strip()

        # Extract time if "at" is present
        if 'at' in time_input:
            time_part = time_input.split('at')[1].strip()
            # Remove any dots from a.m./p.m.
            time_part = time_part.replace('.', '')
            # Remove any spaces between number and AM/PM
            time_part = time_part.replace(' pm', 'pm').replace(' am', 'am')
            
            # Extract hour
            hour_str = ''.join(filter(str.isdigit, time_part))
            if not hour_str:
                raise ValueError("Could not extract hour from time input")
            
            hour = int(hour_str)
            
            # Handle PM times
            if 'pm' in time_part or 'p.m' in time_part:
                if hour != 12:
                    hour += 12
            # Handle AM times
            elif 'am' in time_part or 'a.m' in time_part:
                if hour == 12:
                    hour = 0
            
            reminder_time = reminder_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return reminder_time
    except Exception as e:
        raise ValueError(f"Could not understand time format: {time_input}")
