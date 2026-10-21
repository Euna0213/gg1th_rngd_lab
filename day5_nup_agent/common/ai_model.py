from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# from common.config import (
#     API_KEY,
#     BASE_URL,
#     MODEL,
#     EMBEDDING_MODEL,
# )
from common.config import (
    BASE_URL,
    MODEL
)

def get_llm_model(
    model: str = MODEL,
    temperature: float = 0,
    max_tokens: int = 2048
):
    return ChatOpenAI(
        model=model,
        base_url=BASE_URL,
        temperature=temperature,
        use_responses_api=False,  # base url로 할 때는 이부분 넣어야 함.(MonoRouter 사용)
        max_tokens=max_tokens,
    )


# def get_embedding_model():
#     embedding_model = EMBEDDING_MODEL
#     embeddings = OpenAIEmbeddings(
#         api_key=OPENAI_API_KEY,
#         # base_url=BASE_URL,
#         model=embedding_model
#         )
#     # print(embeddings)
#     return embeddings