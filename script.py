import re

import requests
import wikipediaapi
from bs4 import BeautifulSoup

max_clicks = 3


def search(start, end):
    """BFS search"""
    wiki = wikipediaapi.Wikipedia('ru')
    queue = [[start]]
    explored = []

    if start == end:
        print('Same link')
        return

    while queue:
        path = queue.pop(0)
        node = path[-1]
        if node not in explored:
            page = wiki.page(node)
            neighbours = list(page.links.keys())

            for neighbour in neighbours:
                new_path = list(path)
                new_path.append(neighbour)
                queue.append(new_path)
                if neighbour == end:
                    return new_path

    print('Cant find route')
    return


def run(start_link, end_link):
    wiki = wikipediaapi.Wikipedia('ru')
    slashes_start_link = [x for x, v in enumerate(start_link) if v == '/']
    slashes_end_link = [x for x, v in enumerate(end_link) if v == '/']
    title_start_link = start_link[slashes_start_link[-1]+1:]
    title_start_link = title_start_link.replace('_', ' ')
    title_end_link = end_link[slashes_end_link[-1]+1:]
    title_end_link = title_end_link.replace('_', ' ')

    path = search(title_start_link, title_end_link)
    link_path = [wiki.page(link).fullurl for link in path]
    for i in range(1, len(link_path)):
        current_page = link_path[i-1]
        searched_page = path[i]
        page = requests.get(current_page)
        soup = BeautifulSoup(page.content, 'html.parser')
        parent_text = soup.find('a', title=searched_page).parent.parent.text
        sentences = re.split('[.?!\n] ?', parent_text)
        word = soup.find('a', title=searched_page).text
        sentence = [s for s in sentences if word in s]

        print(sentence[0])
        print(link_path[i])


if __name__ == '__main__':
    start_link = input()
    end_link = input()
    run(start_link, end_link)
