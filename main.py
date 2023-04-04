import json
import os
import shutil
import sqlite3
from collections import defaultdict

import graphviz
import requests
from itertools import chain, product

from bs4 import BeautifulSoup


def parse_table():
    url = 'https://de.wikipedia.org/wiki/Liste_von_Disstracks_des_deutschen_Hip-Hops'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.findAll('table')

    diss_matrix = []
    for tr in table[0].findAll('tr'):
        row = []
        for td in tr.findAll('td'):
            row.append(td.get_text().replace('\n', ''))

        if len(row) == 5:
            diss_matrix.append(row)

    result = [
        {
            'jahr': row[0],
            'title': row[1],
            'von': splitnames(row[2]),
            'gegen': splitnames(row[3]),
            'anmerkung': row[4]
        }
        for row in diss_matrix
    ]
    # print(json.dumps(result, indent=4))
    return result


def splitnames(names):
    return names.replace(' & ', ', ').split(', ')


def generate_diagram(diss_track_list):
    graph = graphviz.Digraph(
        'german-diss-track',
        engine='circo',
        format='svg',
        comment='Diss-Tracks der deutschen Hiphop-Szene'
    )

    rappers = set()
    diss_count = defaultdict(int)

    disses = []
    for diss_track in diss_track_list:
        for rapper in chain(diss_track['von'], diss_track['gegen']):
            if not rapper in rappers:
                graph.node(rapper)
                rappers.add(rapper)
            for src, dst in product(diss_track['von'], diss_track['gegen']):
                tuple = (str(src), str(dst))
                diss_count[tuple] += 1
                disses.append(tuple)

    for (src, dst), weight in diss_count.items():
        graph.edge(src, dst, weight=str(weight))

    # print(graph.source)
    # graph.render(directory='build', view=True)
    return disses


def main(name):

    shutil.rmtree("build", ignore_errors=True)
    os.mkdir('build')
    diss_track_list = parse_table()
    xs = generate_diagram(diss_track_list)

    con = sqlite3.connect("build/diss.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE diss_track(src, dst)")
    cur.executemany("INSERT INTO diss_track VALUES(?, ?)", xs)
    cur.execute('CREATE VIEW disser AS select src as rapper, count(src) as dissing from diss_track GROUP BY src ORDER by count(src)')
    cur.execute('CREATE VIEW dissed AS select dst as rapper, count(dst) as dissed from diss_track GROUP BY dst ORDER by count(dst)')
    cur.execute('CREATE VIEW rapper_heat_map AS select disser.rapper as rapper, dissing, dissed, dissing + dissed as activity, CAST(dissing as REAL) / CAST(dissed as REAL) as diss_factor FROM disser INNER JOIN dissed ON disser.rapper = dissed.rapper ORDER BY activity;')
    con.commit()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
