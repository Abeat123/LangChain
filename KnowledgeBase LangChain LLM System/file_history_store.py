import os,json
from typing import Sequence

from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory



def get_history(session_id):
    return FileChatMessagehistory(session_id,"./chat_history")

class FileChatMessagehistory(BaseChatMessageHistory):
    def __init__(self,session_id,storage_path):

        self.session_id = session_id
        self.storage_path = storage_path
        self.file_path = os.path.join(self.storage_path,self.session_id)

        # 确保文件夹是存在的
        os.makedirs(os.path.dirname(self.file_path),exist_ok=True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:

        #Sequence序列 类似list、tuple
        all_messages = list(self.messages)      # 已有的消息列表
        all_messages.extend(messages )           # 将新的消息添加到已有的消息列表中

        new_messages = [message_to_dict(msg) for msg in all_messages]

        # 将数据写入文件
        with open(self.file_path,'w',encoding='utf-8') as f:
            json.dump(new_messages,f)        # 把字典转成json 写入到文件里

    # 打开文件读取消息文件，然后把所有消息转换成消息列表---[消息、消息.....]
    @property
    def messages(self):
            # 当前文件内 list[字典]
            try:
                with open(self.file_path,'r',encoding='utf-8') as f:
                    message_data = json.load(f)        # 当前文件内的返回值都是： list[字典]
                    messages = messages_from_dict(message_data)
                    return messages

            except FileNotFoundError as e:
                return []

    def clear(self) -> None:
        with open(self.file_path,'w',encoding='utf-8') as f:
            json.dump([],f)