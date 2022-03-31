# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import json
import urllib.parse
import urllib.request
from urllib.request import Request, urlopen
from tqdm import tqdm
import traceback
import time
import re
from urllib.parse import unquote
import os
import string
import argparse

def remove_text_inside_brackets(text, brackets="[]<>{}"):
    count = [0] * (len(brackets) // 2) # count open/close brackets
    saved_chars = []
    for character in text:
        for i, b in enumerate(brackets):
            if character == b: # found bracket
                kind, is_close = divmod(i, 2)
                count[kind] += (-1)**is_close # `+1`: open, `-1`: close
                if count[kind] < 0: # unbalanced bracket
                    count[kind] = 0  # keep it
                else:  # found bracket to remove
                    break
        else: # character is not a [balanced] bracket
            if not any(count): # outside brackets
                saved_chars.append(character)
    return ''.join(saved_chars)

def handle_404(title):
    result = requests.get(f'https://en.wikipedia.org/wiki/{title}')
    if 'error":{"code":"missingtitle"' in result.text:
        with open('data/404ed.json', "a", encoding='utf-8') as data_404:
            data_404.write(json.dumps(event,ensure_ascii=False))
            data_404.write("\n") 
            return None
    else:
        return result




parser = argparse.ArgumentParser()

parser.add_argument("-input", "--input", help="Input name")
parser.add_argument("-output_dir", "--output_dir", help="Output name")

args = parser.parse_args()

f = open("logs/full_TEXT_log.err", "a")
###write into a new file
path=args.input
input_file = path.split('/')[-1]
output_dir = args.output_dir
# output = output_dir+'EKG_DKB_corrected_TEXT.json'
output = (output_dir+input_file).replace('simple','full')

timeout_list = []

output_set = set()

print(output)
if os.path.isfile(output):
    with open(output,'r',encoding='utf-8') as files:
        for line in files:
            temp_table = json.loads(line.strip('\n'))
            # output_set.add(temp_table["wikipediaLabel"][0]["mainsnak"])
            output_set.add(temp_table["wikipediaLabel"])

with open(path, 'r', encoding='utf-8') as files:
    for event in tqdm([json.loads(line.strip('\n')) for line in files]):    
        invalid_strings = ['http : //', 'https : //', 'redlink = 1', '# cite_note', 'action = edit', '# ref_', '<']
        # if any(ele in new_text for ele in invalid_strings) or "was not found on this server" in new_text or "Redirect to :" in new_text:
        #     title=event["wikipediaLabel"][0]["mainsnak"]
        #     title = title.replace('?','%3F')
        #     text=""
        try:
            if event["wikipediaLabel"] not in output_set:
            # if event["wikipediaLabel"][0]["mainsnak"] not in output_set:
                title=event["wikipediaLabel"]
                # title=event["wikipediaLabel"][0]["mainsnak"]
                title = title.replace('?','%3F')
                title = title.replace(" ","_")
                text=""
                try:
                    result = requests.get(f'http://localhost:8080/wikipedia_en_all_nopic_2021-01/A/{title}', allow_redirects=True)
                    if result.status_code == 302:
                        print('302 error')
                        result = requests.get(f'https://en.wikipedia.org/wiki/{title}')
                    if result.status_code == 429:
                        result = requests.get(f'https://en.wikipedia.org/wiki/{title}')
                    if result.status_code == 404:
                        print(title)
                        print('handling 404')
                        result = handle_404(title)
                        result.encoding = 'utf-8'
                        if not result:
                            continue
                except requests.exceptions.TooManyRedirects as exc:
                    result = requests.get(f'https://en.wikipedia.org/wiki/{title}') 
                
                result.encoding = 'utf-8'
                if result.text:
                    soup = BeautifulSoup(result.text, 'html.parser')
                    redirectMsg = soup.find('div', class_='\\"redirectMsg\\"')
                    #its a redirect from wikipedia api so go to the new page on the localserver
                    if redirectMsg:
                        redirect = redirectMsg.find('ul').find('a')['href'].split("/")[2][:-2]
                        result = requests.get(f'http://localhost:8080/wikipedia_en_all_nopic_2021-01/A/{redirect}', allow_redirects=True)
                        result.encoding = 'utf-8'
                        if result.status_code == 404:
                            result = handle_404(redirect)
                            result.encoding = 'utf-8'
                            if not result:
                                continue
                        soup = BeautifulSoup(result.text, 'html.parser')
                       

                    for table in soup.find_all("table"):
                        table.extract()
                    all_text = soup.find_all("p")
                    invalid_strings = ['http://', 'https://', 'redlink=1', '#cite_note', 'action=edit', '#ref_', ]  
                    invalid_chars = ['\n','\t','\r','\f']
                    for item in all_text:
                        if not any(ele in item.text for ele in invalid_strings) and len(item.text) > 1:
                            text_item = item.text.strip()
                            for char in invalid_chars:
                                text_item = text_item.replace(char,' ')
                            text_item = remove_text_inside_brackets(text_item)
                            text_item = re.sub(' +', ' ', text_item).strip()
                            if len(text_item) == 0:
                                continue
                           
                            if str(text_item[-1]) not in string.punctuation:
                                text_item = text_item+'.'
                            text += text_item + ' '
                    text=text.strip()
                
               

                event["narration"]=text
                with open(output, "a", encoding='utf-8') as data1:
                    data1.write(json.dumps(event,ensure_ascii=False))
                    data1.write("\n")
                # output_set.add(event["wikipediaLabel"][0]["mainsnak"])
                output_set.add(event["wikipediaLabel"])
            # else:
            #     # print(event)
            #     print("Event in output set.")    
                
        except  TimeoutError:
            timeout_list.append(title)
            f.write("timeout error \n")
            f.write('\n')
            f.write(traceback.format_exc())
            f.write('\n\n\n\n')
        except Exception:
            f.write("OTHER EXCEPTION \n")
            f.write(title)
            f.write('\n')
            f.write(traceback.format_exc())
            f.write('\n\n\n\n')
f.write(str(timeout_list))
f.close()