import re
import time
import requests
import numpy as np
import pandas as pd
import pymysql.cursors
from bs4 import BeautifulSoup

# Runtime start
start = time.clock()
print(start)

# Connect to the database
connection = pymysql.connect(user='root', password='abc123', host='127.0.0.1', db='FUTHEAD', cursorclass=pymysql.cursors.DictCursor, charset='UTF8')

# Sending request to futhead.com
FutHead = requests.get('http://www.futhead.com/18/players')

# Parsing the number of pages for fifa 18 players
bs = BeautifulSoup(FutHead.text, 'html.parser')
TotalPages = int(re.sub('\s +', '', str(bs.find('span', {'class': 'font-12 font-bold margin-l-r-10'}).get_text())).split(' ')[1])
print('Number of pages to be parsed: ' + str(TotalPages))

fifa = {
    '10': 'FIFA10',
    '11': 'FIFA11',
    '12': 'FIFA12',
    '13': 'FIFA13',
    '14': 'FIFA14',
    '15': 'FIFA15',
    '16': 'FIFA16',
    '17': 'FIFA17',
    '18': 'FIFA18'
}

with connection.cursor() as cursor:
    # Truncating table before inserting data into the table
    for key, value in fifa.items():
        cursor.execute('''
                  CREATE TABLE IF NOT EXISTS %s (
                       NAME      CHAR(30) CHARACTER SET LATIN1 COLLATE LATIN1_BIN,
                       CLUB      VARCHAR(50),
                       LEAGUE    VARCHAR(50),
                       POSITION  VARCHAR(50),
                       RATING    INTEGER(2),
                       PACE      INTEGER(2),
                       SHOOTING  INTEGER(2),
                       PASSING   INTEGER(2),
                       DRIBBLING INTEGER(2),
                       DEFENDING INTEGER(2),
                       PHYSICAL  INTEGER(2),
                       LOADDATE  TIMESTAMP);
                       ''', (value))
        cursor.execute('TRUNCATE TABLE FIFA18;')

        players = []
        attributes = []

        # Looping through all pages to retrieve players stats and information
        for page in range(1, TotalPages + 1):
            FutHead = requests.get('http://www.futhead.com/' + key + '/players/?page=' + str(page) + '&bin_platform=ps')
            bs = BeautifulSoup(FutHead.text, 'html.parser')
            Stats = bs.findAll('span', {'class': 'player-stat stream-col-60 hidden-md hidden-sm'})
            Names = bs.findAll('span', {'class': 'player-name'})
            Information = bs.findAll('span', {'class': 'player-club-league-name'})
            Ratings = bs.findAll('span', {'class': re.compile('revision-gradient shadowed font-12 fut18')})

            # Calcualting the number of players per page
            num = len(bs.findAll('li', {'class': 'list-group-item list-group-table-row player-group-item dark-hover'}))

            # Parsing all players information
            for i in range(0, num):
                p = []
                p.append(Names[i].get_text())
                strong = Information[i].strong.extract()
                p.append(re.sub('\s +', '', str(Information[i].get_text())).split('| ')[1])
                p.append(re.sub('\s +', '', str(Information[i].get_text())).split('| ')[2])
                p.append(strong.get_text())
                p.append(Ratings[i].get_text())
                players.append(p)

            # Parsing all players stats
            a = []
            for stat in Stats:
                if Stats.index(stat) % 6 == 0:
                    if len(a) > 0:
                        attributes.append(a)
                    a = []
                if stat.find('span', {'class': 'value'}) is None:
                    pass
                else:
                    a.append(stat.find('span', {'class': 'value'}).get_text())
            print('page ' + str(page) + ' is done!')

        for player, attribute in zip(players, attributes):
            cursor.execute('''
                      INSERT INTO FUTHEAD.FIFA18 (
                          NAME, 
                          CLUB, 
                          LEAGUE, 
                          POSITION , 
                          RATING, 
                          PACE, 
                          SHOOTING, 
                          PASSING, 
                          DRIBBLING, 
                          DEFENDING, 
                          PHYSICAL
                      ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                          ''', (*player, *attribute))

        # Dumping the lines into a csv file
        pd.read_sql_query('SELECT * FROM FIFA18;', connection).to_csv(value + '.csv', sep=',', encoding='utf-8', index=False)

        # Commit MYSQL statements
        connection.commit()

# Closing connection to the DB and closing csv file
connection.close()

# Runtime end
print(time.clock() - start)
