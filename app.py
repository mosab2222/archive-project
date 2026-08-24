from datetime import datetime
import io
import os
import sqlite3
import pandas as pd
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    send_file,
    url_for,
)

app = Flask(__name__)

UPLOAD_FOLDER = "uploads/received_requests"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# إعداد قاعدة بيانات SQLite لتخزين الطلبات
DB_NAME = "requests_database.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            content TEXT,
            date TEXT,
            filename TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


@app.route("/")
def home():
  return redirect(url_for("client_page"))


@app.route("/client", methods=["GET", "POST"])
def client_page():
  success = False
  if request.method == "POST":
    client_name = request.form.get("client_name")
    content = request.form.get("content")
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    file = request.files.get("file")
    filename = ""
    if file and file.filename != "":
      filename = file.filename
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      file.save(filepath)

    # حفظ الطلب في قاعدة البيانات
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (client_name, content, date, filename)
        VALUES (?, ?, ?, ?)
    """,
        (client_name, content, date_str, filename),
    )
    conn.commit()
    conn.close()

    success = True

  return render_template("client.html", success=success)


@app.route("/admin")
def admin_page():
  today_str = datetime.now().strftime("%Y-%m-%d")

  # جلب الطلبات من قاعدة البيانات لعرضها في لوحة التحكم
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM orders ORDER BY id DESC")
  requests_list = cursor.fetchall()
  conn.close()

  return render_template(
      "admin.html", requests_list=requests_list, today_str=today_str
  )


@app.route("/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
  conn.commit()
  conn.close()
  return redirect(url_for("admin_page"))


# ميزة تصدير وحفظ نسخة احتياطية بصيغة Excel
@app.route("/export_excel")
def export_excel():
  conn = sqlite3.connect(DB_NAME)
  df = pd.read_sql_query(
      "SELECT id, client_name as 'اسم الجهة', content as 'محتوى الطلب', date"
      " as 'وقت الاستقبال', filename as 'المرفق' FROM orders",
      conn,
  )
  conn.close()

  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="الطلبات الواردة")
  output.seek(0)

  return send_file(
      output,
      mimetype=(
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ),
      as_attachment=True,
      download_name=f"requests_backup_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
  )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
