from collections.abc import AsyncGenerator
from ragbits.agents import Agent, ToolCallResult
from ragbits.chat.api import RagbitsAPI
from ragbits.chat.interface import ChatInterface
from ragbits.chat.interface.types import ChatContext, ChatResponse, LiveUpdateType
from ragbits.core.embeddings import LiteLLMEmbedder
from ragbits.core.llms import LiteLLM, ToolCall
from ragbits.core.prompt import ChatFormat
from ragbits.core.vector_stores import InMemoryVectorStore
from ragbits.document_search import DocumentSearch

from ragbits.chat.interface.ui_customization import (
    UICustomization,
    HeaderCustomization,
    PageMetaCustomization
)

embedder = LiteLLMEmbedder(model_name="azure/text-embedding-3-large")
vector_store = InMemoryVectorStore(embedder=embedder)
document_search = DocumentSearch(vector_store=vector_store)

llm = LiteLLM(model_name="azure/gpt-4.1-mini")
agent = Agent(llm=llm, tools=[document_search.search])

class MyChat(ChatInterface):
    ui_customization = UICustomization(
        # Header customization
        header=HeaderCustomization(
            title="NASA AI Assistant",
            subtitle="",
            logo="🚀"
        ),

        # Welcome message shown when chat starts
        welcome_message=(
            "Hello! I'm your AI assistant.\n\n"
            "How can I help you today? You can ask me **anything**! "
            "I can provide information, answer questions, and assist with various tasks."
        ),

        # Page metadata
        meta=PageMetaCustomization(
            favicon="🚀",
            page_title="NASA AI Assistant"
        )
    )

    async def setup(self) -> None:
        pass
        #await document_search.ingest("web://https://arxiv.org/pdf/1706.03762")

    async def chat(
        self,
        message: str,
        history: ChatFormat,
        context: ChatContext,
    ) -> AsyncGenerator[ChatResponse]:
        async for result in agent.run_streaming(message):
            match result:
                case str():
                    yield self.create_live_update(
                        update_id="1",
                        type=LiveUpdateType.START,
                        label="Answering...",
                    )
                    yield self.create_text_response(result)
                case ToolCall():
                    yield self.create_live_update(
                        update_id="2",
                        type=LiveUpdateType.START,
                        label="Searching...",
                    )
                case ToolCallResult():
                    yield self.create_live_update(
                        update_id="2",
                        type=LiveUpdateType.FINISH,
                        label="Search",
                        description=f"Found {len(result.result)} relevant chunks.",
                    )

        yield self.create_live_update(
            update_id="1",
            type=LiveUpdateType.FINISH,
            label="Answer",
        )

if __name__ == "__main__":
    api = RagbitsAPI(MyChat)
    api.run()