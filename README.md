# Speech-to-Text AI Assistant with Google Sheets Integration

This Python application allows users to ask questions through speech input and get AI-generated responses based on predefined information stored in a Google Sheet.

## Features

- Speech recognition for user input
- Google Sheets integration for context data
- OpenAI GPT-3.5 integration for intelligent responses
- Interactive command-line interface

## Setup Instructions

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Google Sheets API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials and save as `credentials.json` in the project directory

3. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SPREADSHEET_ID=your_google_sheet_id_here
   ```

4. Prepare your Google Sheet:
   - Create a new Google Sheet
   - Add your predefined information
   - Copy the Sheet ID from the URL (the long string between /d/ and /edit)
   - Share the sheet with the email address from your Google Cloud credentials

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. When prompted, speak your question clearly into the microphone

3. The application will:
   - Convert your speech to text
   - Fetch relevant context from Google Sheets
   - Generate an AI response based on the context
   - Display the response

4. Choose whether to continue asking questions or exit

## Requirements

- Python 3.7 or higher
- Microphone for speech input
- Internet connection
- Google Cloud account
- OpenAI API key

## Notes

- Make sure your microphone is properly connected and configured
- The first time you run the application, it will open a browser window for Google authentication
- The application will create a `token.json` file to store your Google credentials 