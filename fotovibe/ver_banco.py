import sqlite3

con = sqlite3.connect("fotovibe.db")
cursor = con.cursor()

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
tabelas = cursor.fetchall()

if not tabelas:
    print("Nenhuma tabela encontrada neste banco.")
else:
    for nome, sql in tabelas:
        print(f"\nTabela: {nome}")
        print(sql)

con.close()