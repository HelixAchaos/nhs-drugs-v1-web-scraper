import csv
import json
from bs4 import BeautifulSoup
import requests
import re

def get_ch_url(main_url):
    ch_href_list = []
    page = requests.get(main_url).text
    soup = BeautifulSoup(page, 'lxml')
    tables = soup.find_all("table", {"cellpadding": "0"})
    for x in tables:
        i = x.find("a")
        if re.search("\d{1,2}\.\d", str(i)):
            # print(i)
            ch_href_list.append(i['href'])
    final_ch_href_list = ch_href_list[2:]

    ch_url_list = []
    for i in final_ch_href_list:
        link = main_url.replace("index.asp", i)
        ch_url_list.append(link)
        # print(link)
    print(ch_url_list)
    return ch_url_list


def get_section_url(main_url, ch_url_list):
    section_cleanup_list = []
    section_list = []
    section_url_list = []
    for url in ch_url_list:
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'lxml')
        tables = soup.find_all("tr")
        for x in tables:
            i = x.find("a")
            if re.search("\d{1,2}\.\d{1,2}", str(i)):
                # print(i.text)
                section_cleanup_list.append(i)
    for z in section_cleanup_list:
        if z not in section_list and "index" in str(z):
            section_list.append(z)

    for y in section_list:
        url = main_url.replace("index.asp", y["href"])
        section_url_list.append(url)

    for i in section_url_list:
        print(i)
    return section_url_list


# data=[]
color_map = {'#00B050': 'Green', '#92D050': 'Lime', '#FFC000': 'Yellow', '#C00000': 'Red'}


def clean_whitespace(string: str):
    return re.sub(r'\s+', ' ', string).strip()


# #FFFFCC
def scrape_section(main_url, section_url_list):
    f = open('hello.csv', 'w', encoding="utf-8", newline='')
    fnames = ['main_url', 'ch_url', 'section_number', 'section_name', 'paragraph_number', 'paragraph_name', 'sub_paragraph_number', 'sub_paragraph_name',
              'generic_molecule', 'Brand', 'formulary_status', 'status_tfl', 'strength', 'desc']
    writer = csv.DictWriter(f, fieldnames=fnames)
    writer.writeheader()

    headers_format = {k: None for k in fnames}
    headers_format['main_url'] = main_url
    for second in section_url_list:
        headers_format['ch_url'] = second
        # headers_format['section_number'] = re.match(r"(\d+\.\d+)$", second)

        seconddata = requests.get(second).content
        soup2 = BeautifulSoup(seconddata, "lxml")

        section_num_name = ''
        for paragraph in soup2.find_all('a'):
            try:
                if paragraph['href'] != re.search(r"(index\.asp\?T=\d{1,2}&S=\d{1,2}(?:\.\d{1,2})+)", second).groups()[0]:  # index.asp?T=05&S=5.0
                    continue
                else:
                    text = paragraph.text.strip()
                    if len(text) > 0:
                        try:
                            number, name = text.split(maxsplit=1)
                            print(f"number={number}")
                        except ValueError:
                            continue

                        last_sec_num = 0

                        if sec_num := re.match(r'(\d{1,2}.\d{1,2})', number):
                            headers_format['section_number'] = sec_num.groups()[0]
                            if para_num := re.search('(\d{1,2}.\d{2})', number):
                                if sub_para_num := re.search(r'(\d{1,2}.\d{2}.\d{2})', number):
                                    headers_format['paragraph_number'] = sub_para_num.groups()[0]
                                    headers_format['paragraph_name'] = name
                                    continue
                                else:
                                    headers_format['paragraph_number'] = ''
                                    headers_format['paragraph_name'] = ''
                                    headers_format['section_number'] = para_num.groups()[0]
                                    headers_format['section_name'] = name
                            else:
                                if headers_format['section_number'] == sec_num:  # and headers_format['section_name'] == name
                                    headers_format['paragraph_number'] = sec_num
                                    headers_format['paragraph_name'] = name
                                headers_format['section_name'] = name
                                headers_format['paragraph_number'] = ''
                                headers_format['paragraph_name'] = ''

            except KeyError:
                continue

        for orange in soup2.find_all("table", class_="MsoNormalTable"):
            try:
                if orange.parent['class'] != ['WordSection1']:
                    continue
            except:
                continue
            # print('asdf')
            rows = orange.find_all('tr')
            for row in rows:
                try:
                    if row.parent.parent['class'] != ['WordSection1']:
                        continue
                except:
                    continue
                cols = row.find_all('td')
                color_matches = re.search(r'(?:background:)(#[\dA-F]{6})', cols[0]['style'])
                if color_matches is not None:
                    color = color_matches.groups()[0]
                else:
                    color = "#FFFFFF"

                cols = [ele.text.strip() for ele in cols]
                if len(cols) < 3:
                    continue
                elif len(cols) == 3:
                    headers_format['desc'] = cols[2]
                else:
                    if re.sub(r'\s+', ' ', ' '.join(cols[3:])) in re.sub(r'\s+', ' ', cols[2]):
                        def gen_json(main_key, rows):
                            # d = {}
                            # for row in rows[1:]:
                            #     d[m[1]].append({k: v for k, v in zip([re.sub(r'\s+', ' ', key).strip() for key in rows[0].split('\n\n\n')], [re.sub(r'\s+', ' ', item).strip() for item in row.split('\n\n\n')])})
                            d = [{k: v for k, v in zip(map(clean_whitespace, rows[0].split('\n\n\n')),
                                                                  map(clean_whitespace, row.split('\n\n\n')))} for row in rows[1:]]
                            json_object = json.loads(str(d).replace("'", '"'))
                            return json.dumps(json_object, indent=2)

                        m = cols[2].split('\xa0')
                        if len(m) == 2:
                            m[0] = re.sub(r'\s+', ' ', m[0]).strip()
                            m[1] = gen_json(m[0], m[1].strip().split('\n\n\n\n'))
                        elif len(m) == 3:
                            if re.sub(r'\s+', ' ', ' '.join(cols[3:])).strip() == re.sub(r'\s+', ' ', m[2]).strip():
                                m[0] = re.sub(r'\s+', ' ', m[0]).strip()
                                m[1] = re.sub(r'\s+', ' ', m[1]).strip()
                                m[2] = gen_json(m[1], m[2].strip().split('\n\n\n\n'))
                            else:
                                m[0] = re.sub(r'\s+', ' ', m[0]).strip()
                                m[1] = gen_json(m[0], m[1].strip().split('\n\n\n\n'))
                                m[2] = re.sub(r'\s+', ' ', m[2]).strip()
                        elif len(m) == 4:
                            m[0] = re.sub(r'\s+', ' ', m[0]).strip()
                            m[1] = re.sub(r'\s+', ' ', m[1]).strip()
                            m[2] = gen_json(m[1], m[2].strip().split('\n\n\n\n'))
                            m[3] = re.sub(r'\s+', ' ', m[3]).strip()
                        headers_format['desc'] = '\n\n'.join(m)
                    else:
                        continue

                if molecule_brand:=re.search(r'([\s\S]+)\(([\s\S]+)\)', cols[1]):
                    headers_format['generic_molecule'], headers_format['Brand'] = map(clean_whitespace, molecule_brand.groups())
                else:
                    headers_format['generic_molecule'] = clean_whitespace(cols[1])
                headers_format['formulary_status'] = cols[0]

                try:
                    headers_format['status_tfl'] = color_map[color]
                except KeyError:
                    continue
                # data.append({cols[1]:[color, cols[0], cols[2]]})
                if any(headers_format.values()):
                    print(headers_format)
                    print(headers_format['desc'])
                    writer.writerow(headers_format)
        # exit(0)


def main():
    main_url = "https://www.medednhsl.com/meded/nhsl_formulary/index.asp"
    ch_url_list = get_ch_url(main_url)
    section_url_list = get_section_url(main_url, ch_url_list)
    scrape_section(main_url, section_url_list)
    # table_clenanup(output_rows)


if __name__ == '__main__':
    main()
