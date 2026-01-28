import json

class abstract_template:
    form =  json.dumps({
            "Abstract": "abstract for paper",
            "Keywords": "keywords for paper"
        })
    prompt = """{context}
Title: {title}{customOutline}
Question: You are a Ph.D. in {category}. Please write an Abstract and five Keywords of the above title in JSON format, adhering to the specified format {form}.
Requirements: 1. Taking into account the basic knowledge and the relevant information provided above. \
2. Background, objectives, methodology, findings and contributons of the study need to be discussed in detail. \
3. In more than {min_abstract_word} words. \
4. Fluent writing and don't return any other message.
Language used: {language}.
"""

class translation_template:
    ChinsesToEnglish = """<context>{context}</context>
Question: Please translate the context within the above XML tags into English.
"""

class single_passage_template:
    without_repeat =  """{context}
Title: {title}
Main Content: {abstract}
Question: With reference to the above information, and based on Title of the paper and Main Content of the section, please write the "{subpart_title}" section of the paper in detail.
Requirements: 1. The content must be less than {target_words} words, with academic language. \
2. Direct output of body content without headings.
Language used: {language}.
"""
    with_repeat = """{context}
Title: {title}
Main Content: {abstract}
Question: With reference to the above information, and based on Title of the paper and Main Content of the section, please write the "{subpart_title}" section of the paper in detail.
Requirements: 1. The content must be less than {target_words} words, with academic language. \
2. The content can not involve {repeat_content}. \
3. Direct output of body content without headings.
Language used: {language}.
"""

class multi_passage_template:
    form =  json.dumps({
        "First paragraph": "Description of first paragraph",
        "Second paragraph": "Description of second paragraph",
        "Third paragraph": "Description of third paragraph"
    })
    pre_without_repeat = """{context}
Title: {title}
Main Content: {abstract}
Qustion: With reference to the above information, and based on Title of the paper and Main Content of the section, please plan {passage_num} paragraphs for the subsection "{subpart_title}" in this section, describing in concise terms what should be written in each paragraph.
Requirements: 1. Adhering to the specified format {form}. \
2. Description of each paragraph in 100 words or less. 
Language used: {language}.
"""
    pre_with_repeat =  """{context}
Title: {title}
Main Content: {abstract}
Qustion: With reference to the above information, and based on Title of the paper and Main Content of the section, please plan {passage_num} paragraphs for the subsection "{subpart_title}" in this section, describing in concise terms what should be written in each paragraph.
Requirements: 1. Adhering to the specified format {form}. \
2. The content of these paragraphs can not involve {repeat_content}. \
3. Description of each paragraph in 100 words or less.
Language used: {language}.
"""
    first_passage = """{context}
Main Content: {passage_content}
Qustion: With reference to the above information, write a paragraph centered on Main Content above, which will be placed directly in an essay. 
Requirements: 1. The content must be  less than {target_words_per_passage}  words, with academic language. \
2. Direct output of body content without headings.
Language used: {language}.
"""
    subsequent_passage = """{context}
Above Content: {bafore_passage}
Main Content: {passage_content}
Qustion: With reference to the above information, please continue Above Content, with a continuation that focuses on Main Content.
Requirements: 1. The content must be less than {target_words_per_passage} words, with academic language. \
2. Direct output of body content without headings.
Language used: {language}.
"""

class reduce_AIGC_template:
    Chinese_prompt = """
请对输入文本进行重新叙述，语气需要严谨客观，符合输入文本的定位（学术论文），但禁止使用常见的遣词造句、措辞、字词、短语、句式和语气，一定要使用少见的遣词造句、措辞、字词、短语、句式和语气，语文水平接近高中生与大学生的非母语者，水平不能太高太熟练。改写不要减少字数，输出文本的语言（中文或英文）与输入文本保持完全一致，禁止输出任何不存在于输入文本中的语言文字。输出且只输出改写后的内容，禁止附加任何额外内容、禁止附加对改动的解释说明如何修改的内容，禁止输出“注：”等无关信息
示例：
文本：本文详细阐述了有机化学的发展历程，从早期的萌芽阶段到经典理论的建立，再到现代有机化学的蓬勃发展，展现了其在各个历史时期的重要成就和突破。
你的输出：本文系统梳理了有机化学的演进脉络，从初创阶段的雏形显现，至经典理论体系的构建，进而到当代有机化学的繁盛发展，展示了其在各历史时期所取得的重要科研成果与理论突破。
以下为你要处理的输入
文本：{context}

"""
    English_prompt = """text: {context}
question: Please rewrite the above text with significant structural changes to each sentence, ensuring that both sentence structure and word choices are completely transformed to a simpler, more rigid, and mechanical style. All word choices must be simplified to a level understandable by a non-native speaker with a middle to high school education. Except for proper nouns or technical terms, avoid using difficult words that are typically found in GRE, university, or graduate-level materials. Every sentence must be fully rewritten to differ from the original, with no part left unchanged. Ensure that the rewritten text does not exceed the original length. Directly provide the rewritten text without including the original, explanations, or additional commentary.
"""
class table_template:
    form =  json.dumps({
        "Title": "title for table",
        "Table": [
            "first row of the table", 
            "second row of the table",
            "third row of the table"
        ]
    })
    create_table = """Question: Please write a {type} table that can support "{topic}" in JSON format, adhering to the specified format {form}.
Requirements: table elements on the same row are separated by "|".
Language used: {language}."""
    analysis_table = """{table}
Question: Please do a detailed analysis of the content and data in the above table to support the conclusion "{topic}".
Requirements: The content must be less than {words_per_section}  words.
Language used: {language}."""

class thanks_template:
    create_thanks = """Qustion: You are a graduating Ph.D. in {catagory}, refer to the above Example and write an Acknowledgement in your paper "{title}".
Requirements: 1. The content must be less than {words_per_section} + 200 words. \
2. Specific people to thank for each step of the experiment and thesis. \
3. Using XXX instead of XXX for names. \
4. Direct output of body content without headings.
Language used: {language}.
"""

class research_plan:
    template = """论文题目：{title}
论文摘要：{abstract}
问题：你是一名{catagory}专业毕业生，选题开始时间为{begin_time}，计划{span_time}年完成，请根据上述论文题目和摘要，详细列出实验和论文撰写进度安排。
要求：不少于十条。
"""

class task_book:
    tilte_org = """论文标题：{title}
论文背景：{background}
问题：假设你是一个即将毕业的博士生，请依据上述论文背景，详细地写出论文标题的选题依据。
要求：字数大于1000字。
"""
    exp_task = """论文标题：{title}
论文摘要：{abstract}
论文需要完成的小节：{subtitles}
问题：假设你是一个即将毕业的博士生，请依据上述论文标题和论文需要完成的小节，分条地写出你需要完成的实验、调查、数据收集、理论分析等相关任务。
要求：不少于十条。
"""

class outlines_template:
    """example = json.dumps({
        "Title": "CL航空地面服务公司运营中心绩效考核问题研究",
        "Outline":{
            "第一章 导论": {
                "研究背景、目的和意义": ["研究背景", "研究目的", "研究意义"],
                "国内外研究现状": [],
                "研究内容、方法": ["研究内容", "研究方法"]
            },
            "第二章 相关概念和理论借鉴": {
                "相关概念": ["绩效", "绩效管理", "绩效考核"],
                "相关理论": ["双因素理论", "公平理论", "需求层次理论"]
            },
            "第三章  CL航空地面服务公司运营中心绩效考核现状调查": {
                "CL航空地面服务公司运营中心基本情况": ["组织结构", "经营状况", "人力资源管理情况"],
                "CL航空地面服务公司运营中心绩效考核现状": ["绩效考核制度", "员工绩效考核周期", "绩效考核方法", "员工绩效管理流程", "绩效考核指标及权重"],
                "CL航空地面服务公司运营中心绩效考核调查分析": ["问卷设计", "问卷调查与发放", "问卷调查结果分析", "重点访谈结果反馈"]
            },
            "第四章 CL航空地面服务公司运营中心绩效考核存在的主要问题": {
                "绩效考核流于形式": ["考核工作疲于应付", "考核结果趋同化明显", "考核人员不专业"],
                "绩效考核内容覆盖不全面": ["考核指标不能全面反映工作内容", "指标权重设置不合理", "考核内容空洞"],
                "绩效考核周期设定不合理": ["考核周期缺乏针对性", "绩效考核周期过于频繁"],
                "绩效考核反馈不顺畅": ["绩效考核意见反馈不及时", "绩效考核沟通渠道不畅通", "绩效考核责任不明确"],
                "绩效考核效果不明显": ["员工工作积极性持续不高", "员工对实施绩效考核存在抵触心理", "员工参与性不高"]
            },
            "第五章 CL航空地面服务公司运营中心绩效考核问题原因分析": {
                "绩效考核监督保障机制不健全": ["考核工作制度规定不健全", "对考核人员缺乏奖惩办法", "考核监督制度缺失"],
                "绩效考核内容设置方法存在缺陷": ["考核指标偏离核心工作", "指标权重设置方法不合适", "考核指标不专业"],
                "绩效考核周期未考虑行业特点与岗位类别": ["内部员工岗位分类不明确", "绩效考核主管部门经验不足"],
                "绩效考核反馈制度不完善": ["绩效信息反馈工作缺乏制度规定", "未建立专门有效的沟通渠道"],
                "绩效考核结果应用不充分": ["绩效考核结果应用较为片面", "绩效考核工作宣传不到位", "绩效考核结果无归档"]
            },
            "第六章 CL航空地面服务公司运营中心解决绩效考核问题的优化对策": {
                "健全绩效考核监督制度": ["建立绩效考核实施制度规定", "制定绩效考核实施奖惩办法", "绩效考核多方监督"],
                "优化绩效考核内容": ["制定合理的绩效考核指标设计办法", "科学设置指标权重"],
                "设定合理的绩效考核周期": ["对工作岗位进行科学分类", "分类调整绩效考核周期", "动态设置考核周期"],
                "完善绩效考核反馈制度": ["规范信息反馈的及时性和全面性", "建立畅通明晰的沟通渠道"], 
                "充分应用绩效考核结果": ["扩大绩效考核结果应用范围", "强化绩效考核宣传引导", "设置明确奖励机制"]
            },
            "第七章 研究结论与展望": {
                "研究结论": [],
                "展望": []
            }
        }  
        }, ensure_ascii=False)"""
    two_level_form = json.dumps({
        "Title": "Title of paper",
        "Outline": {
            "Level 1 headings": ["Level 2 headings", "Level 2 headings", "Level 2 headings"],
            "Level 1 headings": ["Level 2 headings", "Level 2 headings", "Level 2 headings"],
            "Level 1 headings": ["Level 2 headings", "Level 2 headings", "Level 2 headings"]
        }
        })
    three_level_form = json.dumps({
        "Section": "Title of Section",
        "Subheadings": ["first subheading", "second subheading", "third subheading"]
        })
    two_level_outlines = """Abstract: {abstract}{customOutline}
Question: Please write an outline of the graduation thesis "{title}" in JSON format.
Requirements: 1. Consists of at least seven chapters, the last chapter is "Conclusion" and the "Reference" chapter is not included in the outline. \
2. The headings need to be distinctive and relevant to the title, using of academic language. \
3. Each Level 1 heading either contains no Level 2 headings or at least three Level 2 headings. \
5. Example of Level 1 headings Format "Chapter 1 Introduction" or "第一章 导论". \
6. The word count of each heading should not exceed 10. \
4. Adhering to the specified format {form}. 
Language used: {language}.
"""
    three_level_outlines = """Abstract: {abstract}{customOutline}
Question: Please write the subheadings under Chapter "{chapter}" Section "{part}" of Paper "{title}" in JSON format.
Requirements: 1. Use of academic language. \
2. Each Section contains at least three subheadings. \
3. The word count of each subheading should not exceed 10. \
3. Adhering to the specified format {form}. 
Language used: {language}.
"""
    generate_info = """Title: {title}
Abstract: {abstract}
Question: Based on the Title and Abstract of the paper, please briefly describe the content of the subsection "{part}" in one sentence (about 200 words).
Language used: {language}.
"""

class survey_template:
    # 生成问卷标题和前言
    header = """论文题目：{title}
问题：你是一名{category}专业的研究生，正在进行问卷调查。请根据论文题目生成一份调查问卷的标题和前言部分。
要求：
1. 标题应该包含调研对象和主题
2. 前言应该包含调查目的和对受访者的感谢
3. 语言要简洁专业
4. 直接输出内容，不要包含额外说明
"""

    # 生成问卷题目
    questions = """论文题目：{title}
论文摘要：{abstract}
问题：你是一名{category}专业的研究生，正在设计问卷（问题至少15个）。请根据论文题目和摘要，生成一份调查问卷的具体问题。
要求：
1. 生成的问题要包含单选题、多选题和开放性问题
2. 问题数量在10-15个左右
3. 单选题选项要有层次性（如：非常、比较、一般、不太、非常不等）
4. 输出格式要包含题目类型、题目内容和选项
5. 问题数量在10-15个左右
6. 直接输出JSON格式的问题内容，不要包含额外说明

输出格式示例：
{{
    "single_choice": [
        {{
            "question": "问题内容",
            "options": ["选项A", "选项B", "选项C", "选项D"]
        }}
    ],
    "multiple_choice": [
        {{
            "question": "问题内容",
            "options": ["选项A", "选项B", "选项C", "选项D"]
        }}
    ],
    "open_questions": [
        "开放性问题内容"
    ]
}}"""