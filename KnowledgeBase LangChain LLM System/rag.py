from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from langchain_core.documents import Document
from openai.types.live import session_config

from file_history_store import get_history
import config_data as config
from vector_stores import VectorStoreService
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder


def get_prompt(prompt):
    print("=" * 20)
    print(prompt)
    print("=" * 20)
    return prompt

class RagService(object):
    def __init__(self):

        self.vector_service = VectorStoreService(
            embedding= DashScopeEmbeddings(model=config.embedding_model_name)
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的已知参考资料为主，如果没有检索到那么你告诉我一下没有检索到，然后直接回答即可"
                "简洁和专业的回答用户问题。参考资料:{context}。"),
                ("system","并且我提供用户的对话历史记录如下:"),
                MessagesPlaceholder("history"),
                ("user","请回答用户提问:{input}")
            ]
        )
        self.chat_model = ChatTongyi(model = config.chat_model_name)
        self.chain = self.__get_chain()

    def __get_chain(self):
        """获取最 终的执行链"""
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段:{doc.page_content},\n 文档元数据: {doc.metadata}\n\n"
            return formatted_str
 
        def format_for_retrieval(value):
            print(value)
            return value["input"]

        def format_for_prompt(value):
            print(value)
            value1 = {}
            value1["input"] = value["input"]["input"]
            value1["history"] = value["input"]["history"]
            value1["context"] = value["context"]
            return value1
        
        chain = (
            {"input":RunnablePassthrough(),"context": RunnableLambda(format_for_retrieval) | retriever | format_document }
            | RunnableLambda(format_for_prompt) | self.prompt_template | get_prompt | self.chat_model | StrOutputParser()
        )

        # 增强链
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key= "input",
            history_messages_key= "history",
        )
        return conversation_chain


if __name__ == "__main__":
    
    res = RagService().chain.invoke({"input":"羽绒服怎么保养？"},config.session_config)
    print(res)

