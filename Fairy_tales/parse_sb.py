import re
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd


def remove_parentheses(text):
    """
    Remove all blocks of text wrapped in parentheses or brackets, squeeze the spaces and strip the text.
    """
    reP = '(\[[^\]]*\]|\([^\)]*\))'
    reS = '\s+'
    return re.sub(reS, ' ', re.sub(reP, ' ', text.replace('\xa0',' '))).strip()


def get_text(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'}

    response = requests.get(url, headers=headers)
    dom = bs(response.text, 'html.parser')
    dt_list = []
    dt_ = dom.find('dt')
    while dt_:
        dt_dict = {}
        if dt_.name == 'dt':

            name = dt_.next_element
            if len(dt_.find_all('dd')) > 1:
                dt_ = dt_.next.next
                text = remove_parentheses(dt_.next.text)
                dt_ = dt_.findNext()
            else:
                dt_ = dt_.next.next
                text = remove_parentheses(dt_.text)
                dt_ = dt_.findNext()

            dt_dict['Character'] = name
            dt_dict['Speech'] = text
            dt_list.append(dt_dict)
        else:
            dt_ = dt_.findNext()

    df = pd.DataFrame(dt_list)
    return df


url = 'http://www.fpx.de/fp/Disney/Scripts/SleepingBeauty/sb.html'

print(get_text(url))
