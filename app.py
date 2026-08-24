import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/received_requests'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

requests_db = []

# مسار التوجيه التلقائي للصفحة الرئيسية
@app.route('/')
def home():
    return redirect(url_for('client_page'))

@app.route('/client', methods=['GET', 'POST'])
def client_page():
    success = False
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        content = request.form.get('content')
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        file = request.files.get('file')
        filename = ""
        if file and file.filename != '':
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
        requests_db.append({
            'client_name': client_name,
            'content': content,
            'date': date_str,
            'filename': filename
        })
        success = True
        
    return render_template('client.html', success=success)

@app.route('/admin')
def admin_page():
    return render_template('admin.html', requests_list=requests_db)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
