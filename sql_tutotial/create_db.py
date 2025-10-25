#shift + enter 執行段落程式碼
#pip install mysql-connector-python
import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="Aa16792380"
)
cursor = connection.cursor()

# 創建資料庫
cursor.execute("CREATE DATABASE IF NOT EXISTS `test_qq`;")

# 查看所有資料庫
cursor.execute("SHOW DATABASES;")
for record in cursor.fetchall():
    print(record)

# 選擇資料庫
cursor.execute("USE `test_qq`;")

#刪除資料表
cursor.execute("DROP TABLE IF EXISTS `test_table`;")
connection.commit()

# 創建資料表
# 在 Python 中，連續三個雙引號（"""）或三個單引號（'''）用來建立多行字串（multi-line string）。

cursor.execute("""
    CREATE TABLE IF NOT EXISTS `test_table` (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(20)
    );
""")
sql = "INSERT INTO `test_table` (name) VALUES ('小白'),('小黑'),('小黃');"
cursor.execute(sql)
connection.commit()
#取得資料庫所有資料
cursor.execute("SELECT * FROM `test_table`;")
records = cursor.fetchall()   # 取出所有查詢結果
for row in records:
    print(row)

#關閉連線
cursor.close()  
connection.close()