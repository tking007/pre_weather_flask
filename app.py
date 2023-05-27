# -*- coding: utf-8 -*-
# author：Mr king
# datetime： 2023-05-22 0022  23:36
# IDE： PyCharm
# 人生苦短 我用python
import joblib
from flask import Flask, render_template, request, redirect, url_for, jsonify
import matplotlib.pyplot as plt
import io
import base64
from flask_socketio import SocketIO
from flask_socketio import emit
import integrated_script

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def build_plot():
    plot_url_1, plot_url_2 = build_plot_data()

    return render_template('index.html', plot_url_1=plot_url_1, plot_url_2=plot_url_2)


def build_plot_data():
    img_1 = io.BytesIO()
    img_2 = io.BytesIO()
    r = integrated_script.GetModel()
    model = joblib.load('Model.pkl')
    preds = model.predict(r[1])
    all_ave_t = []
    all_high_t = []
    all_low_t = []
    all_rainfall = []
    for a in range(1, 7):
        today = integrated_script.DT.datetime.now()
        time = (today + integrated_script.DT.timedelta(days=a)).date()
        all_ave_t.append(round(preds[a][0], 2))
        all_high_t.append(round(preds[a][1], 2))
        all_low_t.append(round(preds[a][2], 2))
        all_rainfall.append(round(preds[a][3], 2))
    temp = {"ave_t": all_ave_t, "high_t": all_high_t, "low_t": all_low_t, "rainfall": all_rainfall}
    plt.plot(range(1, 7), temp["ave_t"], color="green", label="ave_t")
    plt.plot(range(1, 7), temp["high_t"], color="red", label="high_t")
    plt.plot(range(1, 7), temp["low_t"], color="blue", label="low_t")
    plt.legend()
    plt.ylabel("Temperature(°C)")
    plt.xlabel("day")
    plt.savefig(img_1, format='png')
    img_1.seek(0)
    plt.clf()
    plt.plot(range(1, 7), temp["rainfall"], color="black", label="rainfall")
    plt.legend()
    plt.ylabel("mm")
    plt.xlabel("day")
    plt.savefig(img_2, format='png')
    img_2.seek(0)
    plt.clf()
    plot_url_1 = base64.b64encode(img_1.getvalue()).decode()
    plot_url_2 = base64.b64encode(img_2.getvalue()).decode()
    return plot_url_1, plot_url_2


# @socketio.on('my_event')
# def handle_my_event(data):
#     selected_value = data.get('selected_value')
#     build_plot()
#     plot_url_1, plot_url_2 = build_plot()
#     emit('my_response', {'data': data, 'plot_url_1': plot_url_1, 'plot_url_2': plot_url_2})


@app.route('/submit', methods=['POST'])
def submit():
    selected_value = request.form.get('my_select')
    integrated_script.get_id(id=selected_value)
    return redirect(url_for('ok') + '#show')


@app.route('/index')
def ok():
    return render_template('index.html')


@app.route('/getdata', methods=['POST'])
def show():
    year = []
    month = []
    day = []
    ave_t = []
    high_t = []
    low_t = []
    rainfall = []
    wind = []

    r = integrated_script.GetModel()
    model = joblib.load('Model.pkl')
    preds = model.predict(r[1])
    for a in range(1, 8):
        today = integrated_script.DT.datetime.now()
        time = (today + integrated_script.DT.timedelta(days=a)).date()
        result = preds[a]
        year.append(time.year)
        month.append(time.month)
        day.append(time.day)
        ave_t.append(round(result[0], 2))
        high_t.append(round(result[1], 2))
        low_t.append(round(result[2], 2))
        rainfall.append(round(result[3], 2))
        wind.append(round(result[4], 2))

    return jsonify(year=year, month=month, day=day,
                   ave_t=ave_t,
                   high_t=high_t,
                   low_t=low_t,
                   rainfall=rainfall,
                   wind=wind)


@app.route('/your-server-endpoint', methods=['POST'])
def handle_ajax_request():
    selected_value = request.form.get('selectedValue')
    integrated_script.get_id(id=selected_value)
    plot_url_1, plot_url_2 = build_plot_data()
    show()

    return jsonify(plot_url_1=plot_url_1,
                   plot_url_2=plot_url_2,
                   year=year,
                   month=month,
                   day=day,
                   ave_t=ave_t,
                   high_t=high_t,
                   low_t=low_t,
                   rainfall=rainfall,
                   wind=wind)


if __name__ == '__main__':
    app.run()
