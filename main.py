import speech_recognition as sr
import pyttsx3
import webbrowser
import urllib.parse
import datetime
import requests
import json

assistant_name = "sunday"


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


listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

greeting = f'Hello, I am {assistant_name}, your virtual assistant. How can I help you today?'
NEWS_API_KEY = "2a0be3767ca24e52b8a51b04bc3cf338"

def speak(text):
    engine.say(text)
    engine.runAndWait()

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


speak(greeting)

# Adjust these properties for better speech detection
listener.pause_threshold = 1.0  # Wait 1 second of silence before considering the phrase complete
listener.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider the speech as a phrase
listener.non_speaking_duration = 1.0  # Minimum length of silence to consider speech ended

print("Starting voice recognition... (Press Ctrl+C to exit)")

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
            current_time = datetime.datetime.now().strftime('%I:%M %p')
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


        elif 'goodbye' in command:
            speak('Goodbye, have a nice day!')
            break


run_assistant()

