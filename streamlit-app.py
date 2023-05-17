import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import re

def scrape_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        soup = BeautifulSoup(article.html, 'html.parser')
        headings = [tag.text for tag in soup.find_all(['h1', 'h2', 'h3'])]
        meta_description = soup.find('meta', attrs={'name':'description'})
        if meta_description:
            meta_description = meta_description['content']
        else:
            meta_description = ""
        body_content = soup.find('body').text
        word_count = len(body_content.split())
        return headings, word_count, meta_description
    except Exception as e:
        print(f"Error scraping article: {e}")
        return [], 0, ""

def scrape_google(query):
    api_key = '8e87e954-6b75-4888-bd6c-86868540beeb'
    url = f'https://api.spaceserp.com/google/search?apiKey={api_key}&q={query}&domain=google.fr&gl=fr&hl=fr&resultFormat=json&resultBlocks=organic_results%2Canswer_box%2Cpeople_also_ask%2Crelated_searches%2Cads_results'
    response = requests.get(url).json()
    results = []
    all_titles = []
    all_headings = []
    word_counts = []
    serp_descriptions = []
    meta_descriptions = []
    if 'organic_results' in response:
        for result in response['organic_results']:
            try:
                title = result['title']
                url = result['link']
                serp_description = result['description']
                headings, word_count, meta_description = scrape_article(url)
                all_titles.append(title)
                all_headings.append(' '.join(headings))
                word_counts.append(word_count)
                serp_descriptions.append(serp_description)
                meta_descriptions.append(meta_description)
                results.append((title, url, ' '.join(headings), word_count, '', serp_description, meta_description))
            except:
                continue
    if 'people_also_ask' in response:
        people_also_ask = [item['question'] for item in response['people_also_ask']]
        all_questions = ' '.join(people_also_ask)
        results.append((' '.join(all_titles), '', ' '.join(all_headings), pd.Series(word_counts).median(), all_questions, ' '.join(serp_descriptions), ' '.join(meta_descriptions)))
    if not results:
        return pd.DataFrame(columns=['Title', 'URL', 'Headings', 'Word Count', 'People Also Ask', 'SERP Description', 'Site Meta Description']), {}
    df = pd.DataFrame(results, columns=['Title', 'URL', 'Headings', 'Word Count', 'People Also Ask', 'SERP Description', 'Site Meta Description'])
    df = df.rename(index={df.index[-1]: 'Résumé'})
    last_row = df.iloc[-1]
    last_row_dict = last_row.to_dict()
    df.to_csv(f"Scraped_URLs_From_{query}_SERPS.csv")
    return df, last_row_dict

st.title("Google Scraper and Article Analyzer")
query = st.text_input("Enter search queries (separated by commas):")
if st.button("Scrape Google"):
    keywords = [q.strip() for q in query.split(',')]
    st.write(f"Keywords entered: {keywords}")
    for q in keywords:
        df, last_row_dict = scrape_google(q)
        st.write(f"Results for {q}:")
        st.write(df)
        st.write("\nLast row data:")
        for col, data in last_row_dict.items():
            st.write(f"{col}: {data}")
