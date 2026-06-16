from vector_store import VectorStoreService
from llm_manager import LLMManager
from session_manager import ChatSessionManager
from web_search import WebSearchService

class ChatService:
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        self.vector_store_service.create_vector_store()
        self.retriever = self.vector_store_service.get_retriever(k=5)
        
        self.llm_manager = LLMManager()
        self.session_manager = ChatSessionManager()
        self.web_search = WebSearchService()

    def process_message(self, session_id: str, user_message: str) -> str:
        # 1. Retrieve from local knowledge base
        docs = self.retriever.invoke(user_message)
        context_texts = [doc.page_content for doc in docs]
        context_str = "\n\n---\n\n".join(context_texts)

        # 2. Web search (Tavily) for live/external info
        web_results = self.web_search.search(user_message)

        # 3. Build System Prompt
        system_prompt = (
            "You are NeuroBot, an AI assistant for NeuroScan (a stroke detection project).\n"
            "Answer naturally as a knowledgeable medical assistant. "
            "Do NOT say 'based on the context' or 'according to the retrieved knowledge'.\n\n"
            "KNOWLEDGE BASE CONTEXT:\n"
            f"{context_str}\n\n"
        )

        if web_results:
            system_prompt += (
                "LIVE WEB SEARCH RESULTS (use these for up-to-date info):\n"
                f"{web_results}\n\n"
            )

        # 4. Add user's latest test result if available
        last_result = self.session_manager.get_last_result(session_id)
        if last_result:
            system_prompt += (
                "USER'S LATEST NEUROSCAN TEST RESULT:\n"
                f"Risk Probability: {last_result.get('prediction', {}).get('percentage', 'N/A')}%\n"
                f"Risk Level: {last_result.get('prediction', {}).get('risk_level', 'N/A')}\n"
                f"Features:\n{last_result.get('features', {})}\n\n"
                "You may refer to this test result if the user asks about it."
            )

        # 5. Get history and generate response
        history = self.session_manager.get_history(session_id)
        assistant_response = self.llm_manager.generate_response(
            system_prompt=system_prompt,
            chat_history=history,
            user_message=user_message
        )

        # 6. Save to history
        self.session_manager.add_message(session_id, "user", user_message)
        self.session_manager.add_message(session_id, "assistant", assistant_response)

        return assistant_response

    def update_test_result(self, session_id: str, result_data: dict):
        self.session_manager.set_last_result(session_id, result_data)
