import asyncio
from pydantic import BaseModel
from ragbits.core.llms import LiteLLM
from ragbits.core.prompt import Prompt

class ArticleParserPromptInput(BaseModel):
    article_content: str

class ArticleParserPromptOutput(BaseModel):
    abstract: str
    keywords: list[str]
    key_findings: list[str]
    results: str

class QuestionAnswerPrompt(Prompt[ArticleParserPromptInput, ArticleParserPromptOutput]):
    system_prompt = """
    You are an expert science article extractor.
    Your goal is to extract the information from the provided article.
    """
    user_prompt = """
    Article: {{ article_content }}
    """

async def main() -> None:
    llm = LiteLLM(model_name="azure/gpt-4.1-mini", use_structured_output=True)

    with open("data/test.xml") as f:
        article_content = f.read()

    prompt = QuestionAnswerPrompt(ArticleParserPromptInput(article_content=article_content))
    response = await llm.generate(prompt)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
