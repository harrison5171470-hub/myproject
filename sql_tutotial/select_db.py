import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="Aa16792380",
    database="test_qq"
)
cursor = connection.cursor()

#取得資料庫所有資料
cursor.execute("SELECT * FROM `test_table`;")