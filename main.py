import json
import random
import pandas as pd
par = json.load(open("paragraphs_filtered.json", 'r', encoding='utf-8'))
print(len(par))
pages = json.load(open("works.json", 'r', encoding='utf-8'))
page_dict = {}
for page_id in pages.keys():
    page = pages[page_id]
    page['paragraph_cnt'] = 0
    page_dict[page['title']] = page
for item in par:
    work = page_dict[item['title']]
    item['category'] = work['category']
    item['id'] = work['pageid'] * 10 + work['paragraph_cnt']
    work['paragraph_cnt'] += 1
    item['paragraph'] = item['paragraph'].replace("&ndash;", "").replace("&mdash;", "").replace("&#8209;", "-")
# lost = 0
# for title in works.keys():
#     pars = works[title]
#     set_pars = set(pars)
#     if len(set_pars) < len(pars):
#         print(title, len(pars) - len(set_pars))
#         print(pars)
#         lost += len(pars) - len(set_pars)
# print(lost)
random.shuffle(par)
df = pd.DataFrame(par)
df = df.iloc[:, [5, 1, 0, 2, 4, 3]]
df = df.rename(columns={"id": "ID", "author": "Author", "title": "Title", "publication_year": "Pub Year", "paragraph" : "Excerpt", "category" : "Categ"})
print(df)
df.to_excel('output.xlsx', index=False)


