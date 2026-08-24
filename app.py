from datetime import datetime
import os
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

app = Flask(__name__)
# مفتاح سري ضروري لتفعيل جلسات الدخول (Sessions)
app.secret_key = "archive_system_secure_key_2026"

UPLOAD_FOLDER = "uploads/received_requests"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# قاعدة بيانات الشركات المعتمدة للنظام (الإيميل، كلمة المرور، اسم الشركة)
users_db = {
    "company1@admin.com": {"password": "123", "name": "شركة الفرات الهندسية"},
    "company2@admin.com": {"password": "123", "name": "شركة النور للمقاولات"},
}

requests_db = []


# التوجيه التلقائي لصفحة تسجيل الدخول
@app.route("/")
def home():
  return redirect(url_for("login_page"))


# مسار تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login_page():
  error = None
  if request.method == "POST":
    email = request.form.get("email")
    password = request.form.get("password")

    if email in users_db and users_db[email]["password"] == password:
      session["user_email"] = email
      session["company_name"] = users_db[email]["name"]
      return redirect(url_for("admin_page"))
    else:
      error = "البريد الإلكتروني أو كلمة المرور غير صحيحة!"

  return render_template("login.html", error=error)


# تسجيل الخروج
@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("login_page"))


# صفحة العميل (مع إرسال قائمة الشركات ليختار العميل لمن يوجه الطلب)
@app.route("/client", methods=["GET", "POST"])
def client_page():
  success = False
  if request.method == "POST":
    client_name = request.form.get("client_name")
    content = request.form.get("content")
    target_company = request.form.get(
        "company_email"
    )  # الشركة المستهدفة بالطلب
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    file = request.files.get("file")
    filename = ""
    if file and file.filename != "":
      filename = file.filename
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      file.save(filepath)

    requests_db.append({
        "company_email": target_company,
        "client_name": client_name,
        "content": content,
        "date": date_str,
        "filename": filename,
    })
    success = True

  return render_template("client.html", users_db=users_db, success=success)


# لوحة تحكم الأدمن (محمية وتعرض طلبات الشركة المسجلة دخلوها فقط)
@app.route("/admin")
def admin_page():
  if "user_email" not in session:
    return redirect(url_for("login_page"))

  current_email = session["user_email"]
  today_str = datetime.now().strftime("%Y-%m-%d")

  # فلترة الطلبات الخاصة بالشركة الحالية فقط
  company_requests = [
      req for req in requests_db if req.get("company_email") == current_email
  ]

  return render_template(
      "admin.html",
      requests_list=company_requests,
      today_str=today_str,
      company_name=session.get("company_name"),
  )


# مسار حذف طلب (مع التأكد من ملكية الشركة للطلب)
@app.route("/delete/<int:index>", methods=["POST"])
def delete_order(index):
  if "user_email" not in session:
    return redirect(url_for("login_page"))

  current_email = session["user_email"]
  # إيجاد الطلب الحقيقي داخل القائمة العامة وحذفه بأمان
  if 0 <= index < len(requests_db):
    if requests_db[index].get("company_email") == current_email:
      requests_db.pop(index)

  return redirect(url_for("admin_page"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
