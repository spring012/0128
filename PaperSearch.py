from semanticscholar import SemanticScholar

class PaperSearch():
    def __init__(self, search_pattern):
        self.search_pattern = search_pattern
        self.sch = SemanticScholar()
        self.results = self.sch.search_paper(search_pattern)
        self.count = 0


    def get_paper(self, num):
        return self.results[0:num]

    def get_abstract(self, num):
        return [paper.abstract for paper in self.get_paper(num)]

    def get_title(self, num):
        return [paper.title for paper in self.get_paper(num)]

    def get_authors(self, num):
        return [paper.authors for paper in self.get_paper(num)]

    # def get_info_list(self, num):
        info_list = []

        if num > len(self.results):
            num = len(self.results)
        if len(self.results) == 0:
            return info_list
        while(num!=0):
            if(self.results[self.count].abstract != None):
                info_dict = {
                    'title': self.results[self.count].title,
                    'reference': f"[{self.count+1}]{self.results[self.count].title}",
                    'abstract': self.results[self.count].abstract
                }
                num -= 1
                info_list.append(info_dict)
            else:
                self.count += 1
        self.count = 0
        return info_list
    
    def get_info_list(self, num):
        info_list = []
        if len(self.results) == 0:
            return info_list  # 没有搜索结果，返回空列表

        num_collected = 0  # 统计已经收集的论文数
        while num_collected < num and self.count < len(self.results):
            paper = self.results[self.count]

            try:
                if paper.abstract: 
                    authors = getattr(paper, "authors", [])
                    if len(authors) > 2:
                        author_names = f"{authors[0]['name']}, {authors[1]['name']}, et al."
                    elif len(authors) == 2:
                        author_names = f"{authors[0]['name']} and {authors[1]['name']}"
                    elif len(authors) == 1:
                        author_names = authors[0]['name']
                    else:
                        author_names = "Unknown Author"

                    title = getattr(paper, "title", "No Title")
                    year = getattr(paper, "year", "n.d.")
                    journal = getattr(paper.journal, "name", "Unknown Journal") if paper.journal else "Unknown Journal"
                    doi = getattr(paper, "doi", "No DOI available")
                    url = getattr(paper, "url", "No URL available")

                    # IEEE 格式参考文献
                    reference = f"[{self.count+1}] {author_names}, \"{title},\" in *{journal}*, {year}. DOI: {doi}. URL: {url}"

                    info_list.append({
                        'title': title,
                        'reference': reference,
                        'abstract': paper.abstract
                    })
                    num_collected += 1  

            except Exception as e:
                print(f"Error processing paper {self.count}: {e}")

            self.count += 1  

        self.count = 0  
        return info_list
