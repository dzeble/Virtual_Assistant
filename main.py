#imports
import speech_recognition as sr
import pyttsx3
import webbrowser
import urllib.parse
import requests
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pickle
from actions.assistant_actions import save_note, get_news, get_wikipedia_summary, get_google_calendar_service, create_calendar_reminder, parse_time
from transformers import pipeline

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

#function for the assistant to speak
def speak(text):
    engine.say(text)
    engine.runAndWait()

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

