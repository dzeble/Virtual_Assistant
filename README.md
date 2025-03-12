# Virtual Assistant

## Overview
The Virtual Assistant is a Python-based application designed to assist users through voice commands. It can perform various tasks such as playing media, providing news updates, taking notes, and answering questions using information from Wikipedia.

## How It Works
The assistant utilizes speech recognition to listen for user commands and responds using text-to-speech capabilities. The application processes commands to perform actions like searching for information, taking notes, and retrieving news based on user queries.

## Tools Used
- **Python**: The core programming language for the application.
- **SpeechRecognition**: For converting spoken language into text.
- **pyttsx3**: For text-to-speech conversion.
- **Webbrowser**: To open web pages in the default browser.
- **Requests**: To make HTTP requests for fetching news and other data.
- **Google API Libraries**: For managing calendar reminders.
- **Transformers**: For advanced NLP capabilities (if applicable).

## How to Use It
1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/dzeble/Virtual_Assistant.git
   ```
   
2. **Navigate to the Project Directory**:
   ```bash
   cd Virtual_Assistant
   ```
   
3. **Install Dependencies**:
   
   ```bash
   pip install -r requirements.txt
   ```
   
4. **Run the Application**:

   Execute the following command to start the assistant:

   ```bash
   python main.py
   ```
   
5. **Interact with the Assistant**:

   Speak commands such as:
   
   - "Hello" to greet the assistant.
   - "Play [song name]" to play a song on YouTube.
   - "What time is it?" to get the current time.
    - "Tell me about [topic]" to get a summary from Wikipedia.
    - "Take note" to save a note.
    - "News" to get the latest news updates.

