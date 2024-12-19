from flask import Flask, render_template
import csv

app = Flask(__name__, template_folder='./')

@app.route('/')
def index():
    with open('f1_drivers_stats.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        rows = list(reader)

    headers = rows[0] if len(rows) > 0 else []
    data = rows[1:] if len(rows) > 1 else []

    return render_template('index.html', headers=headers, data=data)

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
