import os
import json
from google.oauth2.credentials import Credentials  # type: ignore
from google.oauth2 import service_account  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from dotenv import load_dotenv
from typing import Dict, List, Optional

# from google.oauth2.service_account import ServiceAccountCredentials


class GoogleSheetsService:
    def __init__(self):
        load_dotenv(override=True)
        self.SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        self.KNOWLEDGE_SHEET_ID = os.getenv("KNOWLEDGE_SHEET_ID")
        self.QUESTIONS_SHEET_ID = os.getenv("QUESTIONS_SHEET_ID")
        self.KNOWLEDGE_RANGE = "Sheet1!A1:Z1000"
        self.QUESTIONS_RANGE = "Sheet1!A1:Z1000"

    def get_credentials(self):
        """Get credentials from environment variables."""
        try:
            # Try to get service account credentials
            credentials_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
            if credentials_json:
                credentials_info = json.loads(credentials_json)
                return service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=self.SCOPES
                )

            # If no service account credentials, try to get OAuth2 credentials
            token_json = os.getenv("GOOGLE_SHEETS_TOKEN")
            if token_json:
                token_info = json.loads(token_json)
                return Credentials.from_authorized_user_info(token_info, self.SCOPES)

            raise ValueError("No Google credentials found in environment variables")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials: {e}")
        except Exception as e:
            raise ValueError(f"Error loading credentials: {e}")

    def get_sheet_data(self):
        """Get data from Google Sheets."""
        try:
            credentials = self.get_credentials()
            service = build("sheets", "v4", credentials=credentials)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.KNOWLEDGE_SHEET_ID, range=self.KNOWLEDGE_RANGE)
                .execute()
            )
            return result.get("values", [])
        except Exception as e:
            print(f"Error fetching sheet data: {e}")
            return []

    def _get_sheet_data(self, sheet_id: str, range_name: str) -> List[List[str]]:
        """Get data from Google Sheet."""
        try:
            service = build("sheets", "v4", credentials=self.get_credentials())
            sheet = service.spreadsheets()
            result = (
                sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
            )
            return result.get("values", [])
        except Exception as e:
            print(f"Error getting sheet data: {str(e)}")
            return []

    def get_knowledge_base(self) -> List[Dict[str, str]]:
        """Get formatted knowledge base data."""
        raw_data = self._get_sheet_data(self.KNOWLEDGE_SHEET_ID, self.KNOWLEDGE_RANGE)
        if not raw_data or len(raw_data) < 2:  # Need at least header and one row
            return []

        # Get headers
        headers = raw_data[0]
        knowledge_base = []

        # Process each row
        for row in raw_data[1:]:
            if len(row) >= 2:  # At least question and answer
                item = {
                    "question": row[0],
                    "answer": row[1],
                    "category": row[2] if len(row) > 2 else "General",
                }
                knowledge_base.append(item)

        return knowledge_base

    def get_context_for_response(self) -> List[str]:
        """Get formatted context data for response model."""
        knowledge_base = self.get_knowledge_base()
        context_items = []

        for item in knowledge_base:
            context_str = f"Category: {item['category']}\nQ: {item['question']}\nA: {item['answer']}"
            context_items.append(context_str)

        return context_items

    def format_knowledge_for_prompt(self) -> str:
        """Format knowledge base data for OpenAI prompt."""
        knowledge_base = self.get_knowledge_base()
        formatted_items = []

        for item in knowledge_base:
            formatted_item = f"Category: {item['category']}\nQ: {item['question']}\nA: {item['answer']}"
            formatted_items.append(formatted_item)

        return "\n\n".join(formatted_items)

    def get_questions_history(self) -> List[Dict[str, str]]:
        """Get questions history from Google Sheet."""
        raw_data = self._get_sheet_data(self.QUESTIONS_SHEET_ID, self.QUESTIONS_RANGE)
        if not raw_data or len(raw_data) < 2:
            return []

        headers = raw_data[0]
        history = []

        for row in raw_data[1:]:
            if len(row) >= 2:
                item = {
                    "question": row[0],
                    "answer": row[1],
                    "category": row[2] if len(row) > 2 else "General",
                }
                history.append(item)

        return history
