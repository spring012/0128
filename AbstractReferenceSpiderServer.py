import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

IS_DEBUG = False
SERVER = 'http://10.191.213.82:22020'
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
            requests.post(url, json=data)
            # 超时时间 10分钟
            times = 1
            while True:
                if times > 10:
                    break
                url = SERVER + "/wpg/fetchSearchRes"
                response = requests.post(url)
                result = response.json()
                if result["errCode"] == 0:
                    final_result = result["data"]
                    break
                else:
                    time.sleep(60)
        except Exception as e:
            print(e)
        finally:
            return final_result


def fetchSearchTask():
    try:
        if IS_DEBUG:
            return "KY=xls('传播平台')", "123"
        url = SERVER + "/wpg/fetchSearchTask"
        data = {}
        response = requests.post(url, data=data)
        result = response.json()
        # print(result)
        if result["errCode"] == 0:
            data = result["searchKey"]
            taskId = result["taskId"]
            return data, taskId
        else:
            print("Error: ", result["msg"])
            return None, None
    except Exception as e:
        print(e)
        return None, None


def pushSearchResult(data, taskId):
    try:
        if IS_DEBUG:
            print(data)
            return None
        url = SERVER + "/wpg/pushSearchRes"
        d = {}
        d["result"] = data
        d["taskId"] = taskId
        requests.post(url, json=d)
        return None
    except Exception as e:
        return None


if __name__ == '__main__':

    # 打开网页，开始执行任务
    url = 'https://kns.cnki.net/kns/advsearch?dbcode=CDMD'
    option = webdriver.ChromeOptions()
    # option.add_argument("--headless")
    option.add_argument('window-size=1920x1080')
    # option.add_argument('--start-maximized')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=option)
    # driver = webdriver.Chrome()
    driver.get(url)
    driver.find_element(By.CSS_SELECTOR,
                        'body > div:nth-child(2) > div.main_sh > div > div.sh_mid > div.grade-search-content > div.header > span:nth-child(2)').click()
    time.sleep(2)

    while True:
        # 每20s拉取一次请求
        time.sleep(20)
        searchKey, taskId = fetchSearchTask()
        print("拉取搜索任务" + str(searchKey))
        if searchKey is None or searchKey == "":
            continue
        print("执行搜索任务" + searchKey + "  taskId:" + taskId)

        searchResult = []

        try:
            # sstr = input("请输入要搜索的关键字")
            inputbox = driver.find_element(By.CSS_SELECTOR,
                                           'body > div:nth-child(2) > div.main_sh > div > div.sh_mid > div.grade-search-content > div.right > div.zySearch.container > textarea')
            inputbox.send_keys("1")
            inputbox.clear()
            inputbox.send_keys(searchKey)
            driver.find_element(By.CSS_SELECTOR,
                                'body > div:nth-child(2) > div.main_sh > div > div.sh_mid > div.grade-search-content > div.right > div.zySearch.container > div.rightSearch > div').click()
            time.sleep(2)
            driver.find_element(By.CSS_SELECTOR,
                                '#perPageDiv > ul > li:nth-child(3) > a').click()
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.select_one('#gridTable > div > div:nth-child(2) > div > table')
            rowIndex = 0
            for row in table.select('tr'):
                n = row.select_one('td.name')
                if n is None:
                    continue
                if rowIndex >= 20:
                    break
                # 提取文献名
                name = n.text
                # print(name)
                driver.find_element(By.CSS_SELECTOR,
                                    '#gridTable > div > div:nth-child(2) > div > table > tbody > tr:nth-child(' + str(
                                        rowIndex + 1) + ') > td.operat > a.icon-quote').click()
                time.sleep(4)
                quote = ""
                try:
                    # 提取引用
                    quote = driver.find_element(By.CSS_SELECTOR,
                                                '.quote-pop > div.layui-layer-content > table > tbody > tr:nth-child(1) > td.quote-r').text
                    # print(quote)
                    driver.find_element(By.CSS_SELECTOR, '.layui-layer-close').click()
                    time.sleep(2)
                except Exception as e:
                    print(e)
                    driver.find_element(By.CSS_SELECTOR, '.layui-layer-close').click()
                    time.sleep(2)
                # 提取摘要
                driver.find_element(By.CSS_SELECTOR,
                                    '#gridTable > div > div:nth-child(2) > div > table > tbody > tr:nth-child(' + str(
                                        rowIndex + 1) + ') > td.name > a').click()
                time.sleep(4)
                driver.switch_to.window(driver.window_handles[1])
                summary = ""
                try:
                    gdBtn = driver.find_element(By.CSS_SELECTOR, '#ChDivSummaryMore')
                    if gdBtn is not None:
                        gdBtn.click()
                        time.sleep(2)
                except Exception as e:
                    print(e)
                try:
                    summaryC = driver.find_element(By.CSS_SELECTOR, '#ChDivSummary')
                    if summaryC is not None:
                        summary = summaryC.text
                except Exception as e:
                    print(e)
                finally:
                    # print(summary)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                if summary != "" and quote != "":
                    searchResult.append({"title": name, "reference": quote, "abstract": summary})
                rowIndex += 1
        except Exception as e:
            print(e)
        finally:
            pushSearchResult(searchResult, taskId)
