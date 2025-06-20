import os
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


class WindowedSQLChatHistory(SQLChatMessageHistory):
    def __init__(self, session_id: str, db_url: str, window_size: int = 10):
        super().__init__(session_id=session_id, connection=db_url)
        self.window_size = window_size


class MemoryManager:
    def __init__(self, tenant_id: str, db_url: str = None, window_size: int = 10):
        self.tenant_id = tenant_id
        self.db_url = db_url or os.getenv("YT_DATABASE_URL")
        self.window_size = window_size

    def wrap_with_memory(self, chain):
        """
        Wrap a runnable (agent or chain) with SQL-based chat memory using message history.
        """
        def get_history(session_id: str):
            history = WindowedSQLChatHistory(session_id, self.db_url, self.window_size)
            print(f"Created history for session {session_id}")
            print(f"History messages type: {history.messages}")
            return history

        return RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=get_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )


