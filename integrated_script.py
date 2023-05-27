# -*- coding: utf-8 -*-
# author：Mr king
# datetime： 2023-05-22 0022  23:31
# IDE： PyCharm
# 人生苦短 我用python

from calendar import isleap
import re
from bs4 import BeautifulSoup
import urllib3
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.metrics import mean_absolute_error
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import seaborn as sns
import matplotlib.pyplot as plt
import datetime as DT
import csv


class GetData:
    url = ""
    headers = ""

    def __init__(self, url, header=""):
        """
        :param url: 获取的网址
        :param header: 请求头，默认已内置
        """
        self.url = url
        if header == "":
            self.headers = {
                'Connection': 'Keep-Alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                          '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, '
                              'like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36 ',
                'Host': 'www.meteomanz.com'
            }
        else:
            self.headers = header

    def Get(self):
        """
        :return: 网址对应的网页内容
        """
        # 使用urllib3发送GET请求，返回响应数据
        http = urllib3.PoolManager()
        return http.request('GET', self.url, headers=self.headers).data


def a(t):
    # 将" - "替换为"0"
    return t.replace(" - ", "0")


def get_id(id):
    # 返回城市id，这个函数似乎没有必要，可以直接使用id参数
    data = id
    return id


def write(years, b, c, id="56196"):
    """
    :param id: 城市id，默认为56196（北京）
    :param years: [开始日期距离现在的年份, 结束日期距离现在的年份]
    :param b: [开始日期距离现在日期的天数, 结束日期距离现在日期的天数]
    :param c: csv文件名，用于保存天气数据
    :return: None
    """
     # 打开csv文件，写入表头信息
    f = open(c, 'w', encoding='utf-8', newline='')
    # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(f)
    # 3. 构建列表头
    # "negAve", "negMax", "negMin"
    csv_writer.writerow(["Time", "Ave_t", "Max_t", "Min_t", "Prec", "SLpress", "Winddir", "Windsp", "Cloud"])
     # 计算开始和结束日期，考虑闰年的影响
     # 取当前日期
    today = DT.datetime.today()
    # 闰年片段
    st = isleap(today.year)
    # 取20天前日期
    week_ago = (today - DT.timedelta(days=b[0])).date()
    # 20天后
    week_pre = (today + DT.timedelta(days=b[1])).date()
    if week_ago.month + week_pre.month == 3 or week_ago.month + week_pre.month == 5:
        if week_ago.month == 2 and not st == isleap(today.year - years[0]):
            if st:
                # 今年是，去年或未来不是，所以-1
                week_ago -= DT.timedelta(days=1)
            else:
                # 今年不是，去年或未来是，所以+1
                week_ago += DT.timedelta(days=1)
        if week_pre.month == 2 and not st == isleap(today.year - years[1]):
            if st:
                # 今年是，去年或未来不是，所以要-1
                week_pre -= DT.timedelta(days=1)
            else:
                # 今年不是，去年或未来是，所以+1
                week_pre += DT.timedelta(days=1)
    # 根据日期和城市id构造网址，获取天气数据网页内容
    url = "http://www.meteomanz.com/sy2?l=1&cou=2250&ind=" + id + "&d1=" + str(week_ago.day).zfill(2) + "&m1=" + str(
        week_ago.month).zfill(2) + "&y1=" + str(week_ago.year - years[0]) + "&d2=" + str(week_pre.day).zfill(
        2) + "&m2=" + str(week_pre.month).zfill(2) + "&y2=" + str(week_pre.year - years[1])
    g = GetData(url).Get()
    # 使用BeautifulSoup解析网页内容，提取表格数据，并写入csv文件中
    soup = BeautifulSoup(g, "html5lib")
    # 取<tbody>内容
    tb = soup.find(name="tbody")
    # 取tr内容
    past_tr = tb.find_all(name="tr")
    for tr in past_tr:
        # 取tr内每个td的内容
        text = tr.find_all(name="td")
        flag = False  # 标记是否有无效数据（00/）
        negA = negMax = negMin = False  # 标记是否有负数温度（暂未使用）
         # 对每一列数据进行处理，去除多余的符号或单位，替换缺失值或无效值为2
        for i in range(0, len(text)):
            if i == 0:
                text[i] = text[i].a.string   # 提取日期字符串
                # 网站bug，会给每个月第0天，比如 00/11/2020,所以要drop掉
                if "00/" in text[i]:
                    flag = True  # 如果日期中有00/，则表示无效数据，不写入csv文件中
            elif i == 8:
                # 把/8去掉，网页显示的格式
                text[i] = text[i].string.replace("/8", "")  # 去除云量数据中的/8后缀
            elif i == 5:
                # 去掉单位
                text[i] = text[i].string.replace(" Hpa", "")  # 去除气压数据中的Hpa后缀
            elif i == 6:
                # 去掉风力里括号内的内容
                text[i] = re.sub(u"[º(.*?|N|W|E|S)]", "", text[i].string)  # 去除风向数据中的角度和方向信息，只保留数字
            else:
                # 取每个元素的内容
                text[i] = text[i].string

            # 丢失数据都取2(简陋做法)
            # 这么做 MAE=3.6021
            text[i] = "2" if text[i] == "-" else text[i]  # 将"-"替换为"2"
            text[i] = "2" if text[i] == "Tr" else text[i]  # 将"Tr"替换为"2"
        text = text[0:9]  # 只保留前9列数据，即时间、平均温度、最高温度、最低温度、降雨量、海平面气压、风向、风速和云量
        if not flag:   # 如果没有无效数据，则写入csv文件中
            csv_writer.writerow(text)
    f.close()  # 关闭csv文件


def ProcessData():
    # 用近几年的数据做训练集
    # 如 [1,1], [20, 0]就是用2019年的今天的20天前到2019年的今天数据做训练集
    # 写入csv
    # 调用write函数，分别获取训练集、验证集和测试集的天气数据，并保存为csv文件
    write([1, 1], [15, 0], "weather_train_train.csv")
    write([1, 1], [0, 15], "weather_train_valid.csv")
    write([0, 0], [15, 0], "weather_test.csv")
    # 使用pandas读取csv文件，并将时间列作为索引，并按照日期排序
    # 读取测试集和验证集
    X_test = pd.read_csv("weather_test.csv", index_col="Time", parse_dates=True, dayfirst=True)
    X = pd.read_csv("weather_train_train.csv", index_col="Time", parse_dates=True, dayfirst=True)
    y = pd.read_csv("weather_train_valid.csv", index_col="Time", parse_dates=True, dayfirst=True)

    # 将 '- ' 替换为 '0'
    X_test = X_test.applymap(lambda x: 0 if x == '- ' else x)
    X = X.applymap(lambda x: 0 if x == '- ' else x)
    y = y.applymap(lambda x: 0 if x == '- ' else x)

    # 使用SimpleImputer处理缺失值，使用均值填充
    my_imputer = SimpleImputer()
    # 将训练集和验证集分为特征和目标，并进行缺失值处理
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, test_size=0.2,
                                                          random_state=0)
    imputed_X_train = pd.DataFrame(my_imputer.fit_transform(X_train))
    imputed_X_valid = pd.DataFrame(my_imputer.transform(X_valid))
    imputed_X_train.columns = X_train.columns
    imputed_X_valid.columns = X_valid.columns
    imputed_y_train = pd.DataFrame(my_imputer.fit_transform(y_train))
    imputed_y_valid = pd.DataFrame(my_imputer.transform(y_valid))
    imputed_y_train.columns = y_train.columns
    imputed_y_valid.columns = y_valid.columns
    # 对测试集进行缺失值处理
    imputed_X_test = pd.DataFrame(my_imputer.fit_transform(X_test))

    # 返回处理后的数据集
    return [imputed_X_train, imputed_X_valid, imputed_y_train,
            imputed_y_valid,
            imputed_X_test]


def GetModel(a="Model.pkl"):
    # 调用ProcessData函数，获取处理后的数据集
    [X_train, X_valid, y_train, y_valid, X_test] = ProcessData()
     # 使用随机森林回归模型，设置随机种子和树的数量，并训练模型
    model = RandomForestRegressor(random_state=0, n_estimators=1001)
    # 训练模型
    model.fit(X_train.values, y_train.values)
    # 使用模型对验证集进行预测，并计算平均绝对误差，# 预测模型，用上个星期的数据
    preds = model.predict(X_valid.values)
    # 用MAE评估
    score = mean_absolute_error(y_valid, preds)
     # 保存模型到本地，将模型保存为pkl文件，以便后续使用
    joblib.dump(model, a)
    # 返回平均绝对误差和测试集数据，返回MAE
    return [score, X_test]


if __name__ == '__main__':
    # 设置城市id，默认为北京（56196）
    city_id = '58715'
    # 调用GetModel函数，获取平均绝对误差和测试集数据，并打印平均绝对误差
    r = GetModel()
    print("MAE:", r[0])
     # 加载保存的模型，并对测试集进行预测
    model = joblib.load('Model.pkl')
    preds = model.predict(r[1])
    # 打印未来7天的天气预测结果，包括平均温度、最高温度、最低温度、降雨量和风力
    print("未来7天预测")
    # 创建空列表，用于存储每一天的预测结果
    all_ave_t = []
    all_high_t = []
    all_low_t = []
    all_rainfall = []
    for a in range(1, 8):
        today = DT.datetime.now()
        time = (today + DT.timedelta(days=a)).date()
        all_ave_t.append(round(preds[a][0], 2))
        all_high_t.append(round(preds[a][1], 2))
        all_low_t.append(round(preds[a][2], 2))
        all_rainfall.append(round(preds[a][3], 2))
        # 打印每一天的日期和预测结果
        print(time.year, '/', time.month, '/', time.day,
              ': 平均气温', round(preds[a][0], 2),
              '最高气温', round(preds[a][1], 2),
              '最低气温', round(preds[a][2], 2),
              "降雨量", round(preds[a][3], 2),
              "风力", round(preds[a][4], 2))
    # 创建一个字典，用于存储每一天的平均温度、最高温度、最低温度和降雨量
    temp = {"ave_t": all_ave_t, "high_t": all_high_t, "low_t": all_low_t, "rainfall": all_rainfall}
