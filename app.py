from datetime import datetime
import os
from flask import Flask, redirect, render_template, request, send_from_directory, url_for

app = Flask(__name__)

UPLOAD_FOLDER = "uploads/received_requests"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

requests_db = []


# مسار التوجيه التلقائي للصفحة الرئيسية
@app.route("/")
def home():
  return redirect(url_for("client_page"))


@app.route("/client", methods=["GET", "POST"])
def client_page():
  success = False
  if request.method == "POST":
    client_name = request.form.get("client_name")
    content = request.form.get("content")
    # حفظ التاريخ بصيغة YYYY-MM-DD لمقارنته بسهولة، مع الوقت
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    file = request.files.get("file")
    filename = ""
    if file and file.filename != "":
      filename = file.filename
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      file.save(filepath)

    requests_db.append({
        "client_name": client_name,
        "content": content,
        "date": date_str,
        "filename": filename,
    })
    success = True

  return render_template("client.html", success=success)


@app.route("/admin")
def admin_page():
  # إرسال تاريخ اليوم الحالي للتحقق من الطلبات اليومية
  today_str = datetime.now().strftime("%Y-%m-%d")
  return render_template(
      "admin.html", requests_list=requests_db, today_str=today_str
  )


# مسار حذف طلب بناءً على رقمه في القائمة (Index)
@app.route("/delete/<int:index>", methods=["POST"])
def delete_order(index):
  if 0 <= index < len(requests_db):
    requests_db.pop(index)
  return redirect(url_for("admin_page"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
