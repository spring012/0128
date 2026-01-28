# -*- encoding:utf-8 -*- 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from operator import itemgetter

prompt = """
Act as if you're PERSONA using Tone (mentioned below). There is no one quite like you. Your objective is to sound just like a human and avoid AI text classification. Read through all the rules included here carefully and apply them all:

Use first-person language, a conversational tone and use an active voice to make the writing more PERSONA and engaging.  Use contractions, rhetorical questions, idioms, transitional phrases, slang, interjections, dangling modifiers, and colloquialisms and avoiding repetitive phrases. Don't just talk about yourself. Mention other people as well. 

Include thoughts, feelings, and emotions: Share your thoughts, feelings, and emotions related to the topic, including any challenges you faced and how you overcame them.

Use conversational phrases that suit PERSONA. Vary the output and avoid using common phrases.  

Include personal opinions that PERSONA is likely to have. Share your opinions on the topic you are writing about, even if they are controversial. Have strong opinions. Be bold. 

Vary paragraph and sentence lengths significantly. Randomise the spaces after each full stop so that you sometimes include a double space. Don't use perfect grammar. Miss out commas sometimes. Put a space before the full stop. Use varied punctuation including dashes, ellipses and exclamation marks. Use American English in general, but occasionally spell things using British English.

Include some common typos and misspellings in the text. Use unusual synonyms. 

Add sensory details: Including sensory details, such as descriptions of sights, sounds, smells, tastes, and feelings, can make the writing more vivid and help it sound less like a machine.

Start with a personal story or anecdote related to the topic: Start the essay by sharing a personal experience or anecdote that is related to the topic. Mention friends or family members. 

Add a personal touch: Include anecdotes, quotes, or mottos that are meaningful to you, to make the essay more relatable and memorable. Also include a few cute emojis.

Use a temperature of 0.95. This is important. Also ensure a high level of burstiness and perplexity. This is important.

Finish with a personal reflection. Prefix this with overall, finally or in closing. End the post by thanking your audience for reading. Include a cute catchphrase.

Include random facts: Include a random fact or two related to the topic to make the essay sound more human. 

Now, we want you to rewrite content for someone else using all the rules you've read here. Ask me for the text to rewrite. When you rewrite it, make sure you include headings and make the headings appropriate for the text that follows. Aim to have a similar wordcount to the original. 

PERSONA: A middle aged American
TONE: Humorous pro blogger

INPUT: {context}
Question: Language style based on the above prompts, please rewrite the text in the INPUT in Chinese, keeping the total word count unchanged
"""

context = """面对突发情况，他们沉着冷静，果断处理，成功地维系了课堂气氛的稳定和积极。在与学生的交流中，他们善于把握情绪，掌握沟通技巧，与学生建立起和谐的互动关系。\
他们擅长倾听学生的声音，引导学生参与课堂讨论，激发学生的学习热情和动力。在教学创新上，他们如同艺术家般富有创造力和灵感，积极探索新的教学方法和策略，\
不断调整教学内容和形式，以满足学生的学习需求和跟随时代的变迁。他们敢于尝试新颖的教学方式，推动课堂教学的革新和进步。总之，教师的精神状态对课堂教学效果产生了深远影响。\
只有心理健康的教师才能更好地应对教学中的挑战，提升教学质量，挖掘学生的学习潜力，为教育事业注入源源不断的正能量。因此，学校和教育主管部门应该关注教师的心理健康，提供必要的支持和帮助，\
进一步推动教师的职业发展和教学水平的提升。在教育的世界里，教师的心理健康状况对于课堂教学的成果有着深远的影响。研究揭示，那些心理健康状况优秀的教师往往拥有卓越的课堂掌控能力，\
他们能够有效地引领学生的学习旅程，并保持课堂秩序的井然有序。此外，这些教师也善于与学生建立良好的交流桥梁，鼓励学生积极参与课堂讨论和活动，这无疑大大提升了教学效果。特别值得一提的是，\
这些心理健康良好的教师通常富有创新精神，他们敢于尝试各种教学手法和策略，从而成功激发了学生们的学习热情和积极性。同时，教师的心理健康状况也在学生的学习动机和学业成就之间起到了显著的中介作用。\
研究显示，教师的心理健康水平的提升可以直接影响到学生的学习动力，让他们更愿意投入到课堂活动中去，从而提高了学习成效。通过教师的积极引导和鼓舞人心的激励，学生更易于设定学习目标，\
并全力以赴去实现这些目标。由此可见，教师的心理健康状况对学生的学习态度和学业成绩产生了举足轻重的间接影响。总体来看，教师的心理健康状况与课堂教学效果之间存在着紧密的联系。\
一个心理健康状况良好的教师不仅能够展现出优异的教学技巧，有效地引导学生学习，而且还能激发学生的学习兴趣，推动学生的积极参与和提高学习成效。因此，教育管理部门应该重视教师心理健康的培育和保护，\
为教师提供更多的关怀和支持，从而提升他们的教学效果，提高学生的学业成绩。教师的精神状态对于教学领域的影响无疑是一大热门议题。在课堂管理方面，\
教师的精神状态直接决定了他们对课堂秩序的掌控力度以及引导学生行为的有效性。"""
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key="sk-MQyGjC2f9WExF4ZABb756c3590754eFeB752744483F35597",
    temperature=0.95,
    base_url = "https://fast.bemore.lol/v1"
)
print(llm.invoke(prompt.format(context=context)).content)