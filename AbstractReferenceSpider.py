import requests
import time

IS_DEBUG = False
SERVER = 'http://192.168.0.200:22020'
if not IS_DEBUG:
    SERVER = 'http://60.205.201.163:22020'

class AbstractReferenceSpider:
    def search(self, search_pattern):
        final_result = []
        try:
            url = SERVER + "/wpg/createSearchTask"
            data = {
                "searchKey": search_pattern
            }
            response = requests.post(url, json=data)
            result = response.json()
            taskId = None
            if result["errCode"] == 0:
                taskId = result["taskId"]
            if taskId is None:
                return []
            # 超时时间 10分钟
            times = 1
            while True:
                if times > 10:
                    break
                url = SERVER + "/wpg/fetchSearchRes"
                d = {}
                d["taskId"] = taskId
                response1 = requests.post(url, json=d)
                result1 = response1.json()
                if result1["errCode"] == 0:
                    final_result = result1["data"]
                    break
                else:
                    time.sleep(60)
        except Exception as e:
            print(e)
        finally:
            return final_result