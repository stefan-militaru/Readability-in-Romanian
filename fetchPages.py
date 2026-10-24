import pandas as pd
file = open("booklist.txt", encoding="utf-8")
authors = []
books = []
grades = []
sources = []
for line in file.readlines():
    parts = line.strip("\n").split("/")
    authors.append(parts[1].strip(" ") + " " + parts[0].strip(" "))
    books.append(parts[2].strip(" "))
    grades.append(parts[3].strip(" "))
    sources.append(parts[4].strip(" "))
df = pd.DataFrame({'Author Name' : authors, 'Title': books, "Grade Level": grades, "Source": sources})
wiki_df = df[df["Source"] == "wikisource"]
print(wiki_df)
