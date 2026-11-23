"""
基于Steamlit完成WEB网页上传服务
"""
from unittest import result

import streamlit as st
from openai.types import file_content
from Knowledge_base import KnowledgeBaseService

st.title("知识库更新服务")

uploader_file = st.file_uploader(
    "请上传txt文件",
    type="txt",
    accept_multiple_files=False,
)


if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()

if uploader_file is not None:
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size/1024
    st.subheader(f"文件名：{file_name}")
    st.write(f"文件格式：{file_type},文件大小:{file_size} KB")

    file_content = uploader_file.getvalue().decode("utf-8")
    # st.write(file_content)
    result = st.session_state["service"].upload_by_str(file_content,file_name)

    st.write(result)