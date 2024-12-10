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

#name of the assistant
assistant_name = "sunday"

#countries for news
COUNTRY_CODES = {
    'united states': 'us',
    'uk': 'gb',
    'britain': 'gb',
    'england': 'gb',
    'canada': 'ca',
    'australia': 'au',
    'india': 'in',
    'germany': 'de',
    'france': 'fr',
    'italy': 'it',
    'japan': 'jp',
    'china': 'cn',
    'russia': 'ru',
    'brazil': 'br',
    'mexico': 'mx',
    'ghana': 'gh'
}

#initializing and assigning variables
listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
#greeting from the assistant
greeting = f'Hello, I am {assistant_name}, your virtual assistant. How can I help you today?'
#news api key
NEWS_API_KEY = "2a0be3767ca24e52b8a51b04bc3cf338"
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

#function for the assistant to speak
def speak(text):
    engine.say(text)
    engine.runAndWait()

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



#the assistant greets the user
speak(greeting)

# Adjust these properties for better speech detection
listener.pause_threshold = 1.0  # Wait 1 second of silence before considering the phrase complete
listener.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider the speech as a phrase
listener.non_speaking_duration = 1.0  # Minimum length of silence to consider speech ended

print("Starting voice recognition... (Press Ctrl+C to exit)")

#listens to the user
def listen_to_speech():
    while True:
        try:
            with sr.Microphone() as source:
                print('Adjusting for ambient noise... Please wait')
                listener.adjust_for_ambient_noise(source, duration=1)

                print('Listening... (timeout in 10 seconds if no speech detected)')
                try:
                    voice = listener.listen(source, timeout=10, phrase_time_limit=None)  # No limit on phrase length
                    command = listener.recognize_google(voice)
                    command = command.lower()
                    if assistant_name in command:
                        command = command.replace(assistant_name, '')
                        # print(command)
                except sr.WaitTimeoutError:
                    print("No speech detected within timeout period. Listening again...")
                    continue
                except sr.UnknownValueError:
                    print("Sorry, I couldn't understand that. Please try again.")
                    continue
                except sr.RequestError as e:
                    print(f"Could not request results from speech recognition service; {e}")
                    continue

        except KeyboardInterrupt:
            print("\nStopping voice recognition...")
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            break
        return command

#runs the assistant
def run_assistant():
    while True:
        command = listen_to_speech()
        # print(command)
        if 'hello' in command:
            speak('Hello, how can I help you?')
        elif 'play' in command:
            try:
                # Extract the search query
                search_query = command.replace('play', '').strip()
                # Create the YouTube search URL
                search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
                #below was a funny rick roll
                # search_url = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&search={urllib.parse.quote(search_query)}"
                speak('Playing' + search_query)
                print('Opening YouTube for:' + search_query)
                # Open the URL in the default browser
                webbrowser.open(search_url)
            except Exception as e:
                speak("Sorry, I couldn't play that.")
                print(f"Error playing media: {e}")

        elif 'time' in command:
            current_time = datetime.now().strftime('%I:%M %p')
            speak(f"The current time is {current_time}")
            print(current_time)

        elif any(phrase in command for phrase in ['wikipedia', 'tell me about', 'what is', 'who is']):
            # Remove any of the trigger phrases from the query
            query = command
            for phrase in ['wikipedia', 'tell me about', 'what is', 'who is']:
                query = query.replace(phrase, '').strip()
            
            if query:  # Only search if there's something to search for
                speak("Searching Wikipedia...")
                result = get_wikipedia_summary(query)
                print(f"\nWikipedia Summary: {result}\n")  # Add newlines for better readability
                speak(result)
            else:
                speak("What would you like to know about?")

        elif 'take note' in command or 'save note' in command:
            speak("What would you like me to note down?")
            note_content = listen_to_speech()
            if note_content:
                result = save_note(note_content)
                speak(result)
                print(result)
            else:
                speak("I couldn't hear the note content. Please try again.")

        elif 'news' in command:
            # Check for specific news categories or queries
            categories = ['business', 'technology', 'sports', 'science', 'health', 'entertainment']
            category = next((cat for cat in categories if cat in command), None)

            country_code = 'us'  # default to US
            for country_name, code in COUNTRY_CODES.items():
                if country_name in command.lower():
                    country_code = code
                    break
            
            if 'about' in command or 'search' in command:
                # Extract search query
                query = command.split('about')[-1].strip() if 'about' in command else command.split('search')[-1].strip()
                speak(f"Searching news about {query}")
                news = get_news(query=query, country=country_code)
            elif category:
                speak(f"Getting {category} news from {next(name for name, code in COUNTRY_CODES.items() if code == country_code)}")
                news = get_news(category=category, country=country_code)
            else:
                speak(f"Getting top headlines from {next(name for name, code in COUNTRY_CODES.items() if code == country_code)}")
                news = get_news(country=country_code)
                
            print(f"\n{news}\n")
            speak(news.replace('\n', ' ').replace('   ', ' '))


        elif 'set reminder' in command or 'remind me' in command:
            speak("What should I remind you about?")
            reminder_text = listen_to_speech()
            
            speak("When should I remind you? Please specify the date and time (for example: tomorrow at 3 PM, or December 25th at 9 AM)")
            time_input = listen_to_speech()
            
            try:
                reminder_time = parse_time(time_input)
                success, message = create_calendar_reminder(reminder_text, reminder_time)
                speak(message)
                print(message)
            except ValueError as e:
                speak(f"Sorry, I couldn't understand that time format. {str(e)}")
                print(f"Error parsing time: {str(e)}")
            except Exception as e:
                speak("Sorry, I couldn't set that reminder. Please try again.")
                print(f"Error setting reminder: {e}")


        elif 'goodbye' in command:
            speak('Goodbye, have a nice day!')
            break


run_assistant()

