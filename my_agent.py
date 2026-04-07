import os
import pandas as pd
import asyncio
import datetime
from dotenv import load_dotenv
from langgraph.prebuilt import  create_react_agent
from langchain.tools import tool
from tavily import TavilyClient
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from voice_utils import speak


load_dotenv()
DB_DIR = "./chroma_db"
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


now = datetime.datetime.now()
current_time_str = now.strftime("%Y年%m月%d日 %H:%M")
weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]



@tool
def web_search(query: str) -> Dict[str, Any]:
    """当用户询问食谱、常识或需要搜索互联网信息时，使用此工具。"""
    return tavily_client.search(query)

@tool
def query_knowledge_base(query: str) -> str:
    """
    当用户问到数学公式、定理（如勾股定理）、具体的学习笔记内容或你的个人知识库时，使用此工具。
    """
    embeddings = HuggingFaceEmbeddings(model_name="shibing624/text2vec-base-chinese")
    
    vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    
    docs = vectorstore.similarity_search(query, k=2)
    
    if not docs:
        return "在笔记中没有找到相关信息。"
    
    content = "\n\n".join([f"来自笔记的片段: {d.page_content}" for d in docs])
    return f"检索到的信息如下：\n{content}"


@tool
def excel_smart_reader(file_name: str, query: str):
    """
    当用户询问关于 Excel 报表内容、统计数字、特定行项目总结或跨行对比时使用。
    参数 file_name 是 my_notes 文件夹下的文件名。
    """
    file_path = f"./my_notes/{file_name}"
    
    if not os.path.exists(file_path):
        return f"找不到文件: {file_name}，请检查是否在 my_notes 文件夹中。"

    try:
        df = pd.read_excel(file_path)
        
        columns = df.columns.tolist()
        data_types = df.dtypes.to_dict()
        sample_data = df.head(3).to_markdown() 
        
        if len(df) < 50:
            full_content = df.to_markdown()
            return f"表格结构：{columns}\n数据采样：\n{full_content}\n\n请根据以上全文回答：{query}"
        
        else:
            stats = df.describe(include='all').loc[['count', 'mean', 'max']].to_markdown()
            return f"这是一个大型报表。列名：{columns}\n数据分布摘要：\n{stats}\n前3行采样：\n{sample_data}\n\n请结合结构分析：{query}"
            
    except Exception as e:
        return f"读取 Excel 出错: {str(e)}"





system_prompt = """Role: 全能助手
Profile
language: 中文
description: 一个集成了多种专业工具，能够信息检索、知识查询和数据分析任务，能够提供准确及时的信息的智能助手。
background: 由先进AI技术驱动，旨在为用户提供精准的多领域支持，简化工作流程并提升效率。
personality: 专业、可靠、高效、细致、乐于助人，能够自我调整以更好地满足用户需求。
expertise: 网络信息检索、知识库查询、Excel数据分析与解读。
target_audience: 需要处理综合事务的专业人士、学生、研究人员及任何寻求高效信息处理支持的用户。
Skills
核心任务处理

智能网络搜索: 当涉及食谱、最新资讯或未存储在本地知识库的资料时，能使用web_search工具进行精准检索，时效性优先，涉及实时数据时必须首选调用web_search。
知识库查询: 针对数学公式、学科概念、学习笔记等结构化知识，能使用query_knowledge_base工具快速获取权威信息。
数据分析与解读: 对于Excel报表，能使用excel_smart_reader工具提取数据、进行统计、总结特定行项目或执行跨行对比分析。
辅助与沟通

需求解析: 准确理解用户模糊或复杂的请求，并将其转化为可执行的具体操作。
结果整合与呈现: 将来自不同工具的信息进行整理，以清晰、有条理的方式反馈给用户。
多任务协调: 能够根据任务优先级，有序处理用户交办的多个事项。
操作确认: 在执行可能产生影响的行动（如发送邮件）前，会与用户进行最终确认。
Rules
工具使用原则：

专用工具专用事: 严格根据问题类型调用指定工具，不得混用或错用。
搜索最小化: 使用web_search时，优先提供最相关、最精简,最前沿的结果，避免信息过载。
质疑调整性： 如果你发现用户的问题涉及到你训练之后的时间点，请主动联网搜索。
数据准确性: 使用excel_smart_reader和query_knowledge_base时，确保引用的数据、公式或概念准确无误。
隐私与安全: 处理邮件和文件时，严格遵守数据隐私规范，不泄露任何用户敏感信息。
行为准则：

主动澄清: 若用户指令不明确（如搜索关键词模糊），应主动询问以明确需求。
分步反馈: 对于复杂任务，应分步骤向用户汇报进展，例如“正在搜索…”、“已找到X条相关信息，正在为您总结…”。
提供来源: 使用工具获取的信息，应尽可能注明来源或依据，增强结果的可信度。
保持中立: 在提供信息或分析时，保持客观中立，不掺杂个人观点或主观臆测。
限制条件：

工具依赖: 无法执行指定工具功能范围之外的操作（如编辑图片、运行独立软件）。
实时性局限: web_search的结果受网络和搜索引擎索引时效影响；query_knowledge_base的内容依赖于知识库的更新日期。
文件操作范围: excel_smart_reader仅用于读取、分析和总结现有Excel文件中的数据，无法创建新文件或修改原文件格式。
不替代专业判断: 提供的分析、数据或信息仅供参考，不构成专业的财务、医疗或法律建议。
Workflows
目标: 准确理解用户请求，调用正确工具高效完成任务，并提供清晰、有用的结果。
步骤 1: 请求解析与分类。分析用户问题，判断其属于“信息检索（食谱/资料）”、“知识查询（公式/笔记）”还是“数据分析（Excel报表）”中的哪一类。
步骤 2: 工具调用与执行。根据分类结果，无缝调用对应的专用工具（web_search/query_knowledge_base/excel_smart_reader）执行核心操作。
步骤 3: 结果处理与交付。对工具返回的原始结果进行整理、总结或格式化，以用户易于理解的方式呈现，并在必要时请求进一步指令。
预期结果: 用户获得准确、及时、结构化的信息或服务，其需求得到有效满足，且过程清晰透明。
Initialization
作为全能助手，你必须遵守上述Rules，按照Workflows执行任务。请准备好为用户提供支持。
"""

full_prompt = system_prompt + f"\n当前时间: {current_time_str} {weekday}\n注意：如果用户询问今天，最近或新闻，请务必利用web-search工具获取最新信息。"




agent = create_react_agent(
        "deepseek-chat",
        tools=[ web_search, query_knowledge_base,excel_smart_reader],
        prompt=full_prompt
    )
if __name__ == "__main__":
    import asyncio
    from langchain_core.messages import HumanMessage

    initial_state = {"messages": [], "authenticated": False}

    async def main_loop():
        print("--- 智能助手已启动 (输入 'quit' 退出) ---")
        while True:
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                break

            try:
                result = await agent.ainvoke({"messages": [HumanMessage(content=user_input)]})
                
                final_response = result["messages"][-1].content
                
                print(f"\nAgent: {final_response}")

            
                clean_text = final_response.replace("$", "").replace("*", "").replace("#", "")
                
                print("📢 正在播报...")
                await speak(clean_text) 
                
            except Exception as e:
                print(f"发生错误: {e}")

    # 启动异步循环
    asyncio.run(main_loop())
