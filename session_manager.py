import os
import json

class SessionManager:
    def __init__(self, history_file):
        """
        Initializes the session manager using the given history file.
        Loads existing sessions if available.
        """
        self.history_file = history_file
        self.sessions = []
        self.load_history()

    def load_history(self):
        """Loads existing session history from the JSON file."""
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                try:
                    self.sessions = json.load(f)
                except Exception:
                    self.sessions = []
        else:
            self.sessions = []

    def add_session(self, session_data):
        """Appends the provided session data to the history and writes it to the file."""
        self.sessions.append(session_data)
        with open(self.history_file, "w") as f:
            json.dump(self.sessions, f, indent=4)

    def get_total_suitable(self):
        """Returns the total number of suitable images annotated across all sessions."""
        total = 0
        for session in self.sessions:
            total += session.get("suitable_images", 0)
        return total

    def get_session_count(self):
        """Returns the number of sessions in history."""
        return len(self.sessions)
