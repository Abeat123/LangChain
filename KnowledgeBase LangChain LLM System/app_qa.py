from rag import RagService
import streamlit as st
import config_data as config

st.title("智能客服")
st.divider()

# 列表里存消息，每条消息都是一个字典，包含角色和内容
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role":"assistant","content":"您好！我是您的智能客服，请问有什么可以帮您的？"}]

# 保存状态
if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()

# 历史消息回显
for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input("请输入您的问题：")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role":"user","content":prompt})

    ai_res_list = []

    with st.spinner("智能客服正在思考中..."):

        res_stream = st.session_state["rag"].chain.invoke({"input":prompt},config.session_config)

        def capture(generator,cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk

        st.chat_message("assistant").write_stream(capture(res_stream,ai_res_list))
        st.session_state["messages"].append({"role":"assistant","content":"".join(ai_res_list)})