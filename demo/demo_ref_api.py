import requests

# 构建API请求
query = "城市社区管理模式优化研究——以A社区为例"  # 搜索关键词
url = f"https://api.crossref.org/works?query={query}"  # 构建API请求URL

# 发起API请求
response = requests.get(url)
data = response.json()

# 解析API响应
for item in data['message']['items']:
    # 获取文献信息
    title = item['title'][0]  # 获取文献标题
    abstract = item.get('abstract')  # 获取文献摘要
    dois = item.get('DOI')  # 获取文献的DOI

    # 获取引用信息
    if 'reference' in item:
        references = item['reference']  # 获取文献引用列表
        for ref in references:
            # 处理文献引用信息
            pass

    # 打印文献信息
    print(f"Title: {title}")
    print(f"Abstract: {abstract}")
    print(f"DOI: {dois}")