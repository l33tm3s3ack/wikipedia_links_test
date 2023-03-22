import asyncio
import concurrent.futures
import logging
import re

import requests
import wikipediaapi
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


def wikipage_links(address, request_count):
    wiki = wikipediaapi.Wikipedia('ru')
    logging.info(f'creating request to {address}')
    logging.info(f'count request = {request_count}')
    return list(wiki.page(address).links.keys())


async def explore_path(path, goal, explored, pool, loop, request_count):

    node = path[-1]
    new_paths = []
    goal_path = None
    if node not in explored:
        explored.append(node)
        neighbours = await loop.run_in_executor(
            pool, lambda: wikipage_links(node, request_count)
        )
        for neighbour in neighbours:
            new_path = list(path)
            new_path.append(neighbour)
            new_paths.append(new_path)
            if neighbour == goal:
                goal_path = new_path
        return (goal_path, new_paths, explored)


async def path_set_cycle(path_set, end, explored):
    loop = asyncio.get_running_loop()
    new_path_set = []
    tasks = []
    request_count = 0
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for path in path_set:
            request_count += 1
            tasks.append(
                asyncio.create_task(
                    explore_path(path,
                                 end,
                                 explored,
                                 pool,
                                 loop,
                                 request_count)
                )
            )
        results = await asyncio.gather(*tasks)
        for result in results:
            goal_path, new_paths, explored = result
            if goal_path is not None:
                return (goal_path, new_path_set, explored)
        new_path_set += new_paths
    return (goal_path, new_path_set, explored)


def search(start, end):
    """BFS search"""
    paths = [[start]]
    explored = []

    if start == end:
        print('Same link')
        return

    while paths:
        goal_path, paths, explored = asyncio.run(
            path_set_cycle(paths, end, explored)
        )
        if goal_path is not None:
            return goal_path

    print('Cant find route')
    return


def sentence_search(current_link, searched_title):
    page = requests.get(current_link)
    soup = BeautifulSoup(page.content, 'html.parser')
    parent_text = soup.find('a', title=searched_title).parent.parent.text
    sentences = re.split('[.?!\n] ?', parent_text)
    word = soup.find('a', title=searched_title).text
    sentence = [s for s in sentences if word in s]
    return sentence[0]


def run(start_link, end_link):
    wiki = wikipediaapi.Wikipedia('ru')
    slashes_start_link = [x for x, v in enumerate(start_link) if v == '/']
    slashes_end_link = [x for x, v in enumerate(end_link) if v == '/']
    title_start_link = start_link[slashes_start_link[-1]+1:]
    title_start_link = title_start_link.replace('_', ' ')
    title_end_link = end_link[slashes_end_link[-1]+1:]
    title_end_link = title_end_link.replace('_', ' ')

    path = search(title_start_link, title_end_link)
    if path is None:
        return
    link_path = [wiki.page(title).fullurl for title in path]
    for i in range(1, len(link_path)):
        current_link = link_path[i-1]
        searched_title = path[i]
        print(sentence_search(current_link, searched_title))
        print(link_path[i])


if __name__ == '__main__':
    start_link = input('Start link: ')
    end_link = input('End link: ')
    run(start_link, end_link)
