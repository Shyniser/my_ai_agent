import streamlit as st
from my_agent import agent # 导入你调通的那个 agent
from langchain_core.messages import HumanMessage
import streamlit as st
import os

st.set_page_config(page_title="私人情报官", page_icon="🕵️")

st.title("🕵️ 全能情报官 - 网页版")
st.caption("集成联网搜索、RAG 知识库与数据分析")

# 1. 侧边栏配置
with st.sidebar:
    st.header("系统状态")
    st.success("DeepSeek 已连接")
    st.header("📊 数据上传")
    uploaded_file = st.file_uploader("选择 Excel 文件", type=["xlsx", "xls"])
    if st.button("清理对话历史"):
        st.session_state.messages = []
    if uploaded_file is not None:
        # 确保 my_notes 文件夹存在
        if not os.path.exists("./my_notes"):
            os.makedirs("./my_notes")
        
        # 保存上传的文件到 my_notes 目录
        file_path = os.path.join("./my_notes", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"已上传: {uploaded_file.name}")
        st.info("现在你可以让助手分析这个表了。")


# 2. 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 显示对话历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. 用户输入
if prompt := st.chat_input("问问今天的新闻，或者让我分析数据..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. 调用 Agent 获取回复
    with st.chat_message("assistant"):
        with st.spinner("情报官正在思考/检索中..."):
            # 这里调用你之前的 ainvoke 逻辑
            response = agent.invoke({"messages": [HumanMessage(content=prompt)]})
            ans = response["messages"][-1].content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
