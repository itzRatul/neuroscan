import time

class ChatSessionManager:
    def __init__(self):
        # Maps session_id to {"messages": [{"role": "system", "content": "..."}], "last_result": None}
        self.sessions = {}

    def get_or_create_session(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "last_result": None,
                "created_at": time.time()
            }
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_or_create_session(session_id)
        session["messages"].append({"role": role, "content": content})
        
        # Keep context window manageable (keep last 20 messages)
        if len(session["messages"]) > 20:
            session["messages"] = session["messages"][-20:]

    def get_history(self, session_id: str):
        return self.get_or_create_session(session_id).get("messages", [])

    def set_last_result(self, session_id: str, result_data: dict):
        session = self.get_or_create_session(session_id)
        session["last_result"] = result_data

    def get_last_result(self, session_id: str):
        return self.get_or_create_session(session_id).get("last_result")
