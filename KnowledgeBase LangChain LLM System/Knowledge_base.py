"""
    知识库
"""
import hashlib
import os

from datetime import datetime
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config_data as config
from langchain_chroma import Chroma

def check_md5(md5_str: str):
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w',encoding="utf_8").close()
        return False
    else:
        for line in open(config.md5_path, 'r',encoding="utf_8").readlines():
            line = line.strip()     # 处理字符串前后的空格与回车
            if line == md5_str:
                return True
        return False



def save_md5(md5_str: str):

    """
        将传入的md5 文件追加到 md5字符串中
    """
    with open(config.md5_path, 'a',encoding="utf_8") as f:
        f.write(md5_str + '\n')

def get_string_md5(input_str: str, encoding='utf-8'):
    """将传入的字符串转换成md5数组"""

    # 将字符串转换为bytes字节数组
    str_bytes = input_str.encode(encoding)
    md5_obj = hashlib.md5()     # 得到md5对象
    md5_obj.update(str_bytes)   # 更新内容(传入即将要转换的字节数组)
    md5_hex = md5_obj.hexdigest()   # 得到md5的十六进制字符串

    return md5_hex

class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok=True)
        self.chroma = Chroma(
            collection_name= config.collection_name,
            embedding_function= DashScopeEmbeddings(model="text-embedding-v4"),
            persist_directory= config.persist_directory,
        )
        self.spliter = RecursiveCharacterTextSplitter(      # 配置文本分割
            chunk_size= config.chunk_size,          # 分割后的文本段的最大长度
            chunk_overlap =  config.chunk_overlap,  # 连续文本段之间的字符重叠数量
            separators= config.separators,          # 自然段落划分的符号
            length_function= len                    # 使用python自带的len函数做长度统计
        )

    def upload_by_str(self,data,filename):

        md5_hex = get_string_md5(data,encoding='utf-8')
        if check_md5(md5_hex):
            return "[跳过]内容已经存在知识库中"

        if len(data) > config.max_spliter_char_number:
            Knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            Knowledge_chunks = [data]       # 无需分割

        metadata = {
            "source": filename,
            # 2025-01-01 10:00:00
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "小丁",
        }
        self.chroma.add_texts(      # 内容加载到向量库中
            Knowledge_chunks,
            metadatas = [metadata for _ in Knowledge_chunks]
        )
        save_md5(md5_hex)
        return "[成功]内容已经成功载入向量库"

if __name__ == '__main__':
    service = KnowledgeBaseService()