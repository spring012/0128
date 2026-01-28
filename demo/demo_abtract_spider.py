from AbstractReferenceSpider import AbstractReferenceSpider
import torch
import time

if __name__ == '__main__':
    A = time.time()
    r = AbstractReferenceSpider().search('KY=xls(\'城市社区管理\') OR KY=xls(\'社区治理\') OR KY=xls(\'社区参与\') OR KY=xls(\'服务供给\') OR KY=xls(\'信息化建设\')')
    print(r)
    print(time.time() - A)
    torch.save(r, 'ref_data')
