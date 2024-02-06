#警告过滤
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import datetime as dt
import json
import time
import urllib.request
import prestodb
import requests
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
import seaborn as sns
import six
import altair as alt

#显示中文
import matplotlib as mpl
mpl.rcParams['font.sans-serif'] = ['KaiTi']
mpl.rcParams['font.serif'] = ['KaiTi']


##############################################################################################################################
# 1天气信息获取
##############################################################################################################################
##############################################################################################################################
# 1.1 ACCU
##############################################################################################################################

##############################################################################################################################
#单个城市的天气数据提取
def get_accu_12h_weather(api, location_id):
    url = 'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/%s?apikey=%s&details=true' % (location_id, api)
    with urllib.request.urlopen(url) as url:
        data = json.loads(url.read().decode())
    df_list =[]
    get_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(12):
        pred_time = (dt.datetime.now()+dt.timedelta(hours=1+i)).strftime("%Y-%m-%d %H:%M:%S")
        df_list.append({'source' :'accu',
                        'get_date' :get_time[:10],
                        'get_hour' :get_time[11:13],
                        'pred_date' :pred_time[:10],
                        'pred_hour' :pred_time[11:13],
                        'temperature' : np.round((data[i]['Temperature' ]['Value']-32)/1.8,1),     #华氏转摄氏度
                        'rain' :data[i]['Rain' ]['Value']*25.4,                                    #Inch转MM
                        'rain_proba': data[i]['RainProbability']/100
                       })
    city_weather = pd.DataFrame(df_list, columns=['source' ,'get_date' ,'get_hour' ,'pred_date' ,'pred_hour' ,'temperature' ,'rain', 'rain_proba' ])
    return city_weather

#城市天气数据汇总
def get_accu_forecast_weather(api, locations):
    weather = pd.DataFrame()
    for city_name, city_key in locations.items():
        city_weather = get_accu_12h_weather(api, city_key)
        #城市的名称
        city_weather['city_name'] = city_name
        weather = weather.append(city_weather)
    return weather

##############################################################################################################################


##############################################################################################################################
# 1.2 CAIYUN
##############################################################################################################################

##############################################################################################################################
def Presto(sql):
    conn=prestodb.dbapi.connect(
        host='10.83.99.3',
        port=8080,
        user='CYYG_BI',
        password='kgwVQTOjP8OrYRHD1N3nWUQVW09O277o',
        catalog='hive')
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()    
    return pd.DataFrame(rows)


#彩云原始数据获取
def get_caiyun_source(ymdh):
    sql = '''
        select
            b.city_name as city_name
            ,hour_temperature_48 as temperature
            ,hour_precipitation_48 as rain
        from
            (
            select
                 concat_ws('-',year,month,day,hour) as date_id
                 ,concat(
                        substr(concat_ws('-',year,month,day,hour),1,10)
                        ,' '
                        ,substr(concat_ws('-',year,month,day,hour),12,13)
                        ,':00:00'
                        ) as time_id
                 ,24-cast(substr(concat_ws('-',year,month,day,hour),12,2) as int) as delta
                 ,cityid
                 ,city_name 
                 ,didi_cityid as city_id
                 ,server_time1                   --实时时间
                 ,hour_precipitation_48          --降水
                 ,hour_wind_48_speed             --风速
                 ,hour_pm25_48                   --pm25
                 ,hour_temperature_48
                 ,row_number() OVER (PARTITION BY city_name ORDER BY server_time1 DESC) as rn
            from
                pbs_dw.dwv_weather_h
            where
                concat_ws('-',year,month,day,hour) = '{ymdh}'
                and didi_cityid in (44,290,291,292,293,294,173,295,296,297,298,299,310,311,136,279,137,138,117,118,119,50,53,17,19,280,281,282,283,284,285,286,287,288,300,289,301,302,303,304,305,306,307,82,308,309)
                and city_name in ('成都市','绵阳市','自贡市','宜宾市','普洱市','凉山彝族自治州','怒江傈僳族自治州','德阳市','文山壮族苗族自治州','昆明市','泸州市','西双版纳傣族自治州','广元市','铜仁市','大理白族自治州','玉溪市','安顺市','遂宁市','广安市','眉山市','黔南布依族苗族自治州','内江市','临沧市','资阳市','红河哈尼族彝族自治州','迪庆藏族自治州','达州市','黔东南苗族侗族自治州','德宏傣族景颇族自治州','贵阳市','楚雄彝族自治州','保山市','巴中市','南充市','毕节市','黔西南布依族苗族自治州','乐山市','攀枝花市','昭通市','丽江市','六盘水市','曲靖市','遵义市','雅安市')
            )a 
            
            left join
            (
            select 
                city_id
                ,city_name
            from 
                g_bi.cities_group
            where  
                region='川渝云贵'
            )b
            on a.city_id = b.city_id
        where
            rn =1
    '''
    sql_format = sql.format(ymdh = ymdh)
    data = Presto(sql_format)
    data.columns=['city_name','temperature','rain']
    return data

#######################################################################################
#彩云天气预测数据
def get_caiyun_forecast_weather(data):
    #取出所有的城市
    city_list = list(data.city_name.value_counts().index)
    weather = []
    #循环提取每个城市的数据
    for city in city_list:
        df_city = data[data['city_name']==city]
        df_temp = df_city['temperature' ][df_city['temperature' ].index[0]]
        df_rain = df_city['rain' ][df_city['rain' ].index[0]]
        #温度和降雨的key相同
        key_list = list(df_temp.keys())
        for key in key_list:
            weather.append({'source' :'caiyun',
                           'get_date' :get_time[0:10],
                           'get_hour' :get_time[11:13],
                           'pred_date' :key[0:10],
                           'pred_hour' :key[11:13],
                           'temperature' :df_temp[key],
                           'rain' :df_rain[key],
                           'rain_proba': np.nan,
                           'city_name':city
                          })
    weather = pd.DataFrame(weather, columns=['source' ,'get_date' ,'get_hour' ,'pred_date' ,'pred_hour' ,'temperature' ,'rain', 'rain_proba' ,'city_name'])
    #排序
    weather.sort_values(['city_name','pred_date' ,'pred_hour' ],inplace=True)
    #重置索引
    weather.reset_index(inplace=True,drop=True)
    return weather
##############################################################################################################################


##############################################################################################################################
# 1.3 WEATHER_CHINA
##############################################################################################################################

##############################################################################################################################
def parse_page(url):
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                     'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }
    ALL_DATA = []
    response = requests.get(url,headers=headers)
    text = response.content.decode('utf-8')
    soup = BeautifulSoup(text,'html5lib')            #由于html5lib容错性较好因此用它不用lxml
    conMidtab = soup.find('div',class_ = 'left-div')
    pattern = re.compile(r'var hour3data.', re.MULTILINE | re.DOTALL)
    script = conMidtab.find("script", text=pattern)
    tables = pattern.search(script.text).string     #未来48小时温度等信息，str

    city_name_text = soup.find('title').string
    city_name_1    = city_name_text.split(',')[0][1:5]
    city_name      = city_name_1.replace('天气','市')
    city_name      = city_name.replace('天','市')
    for i in range(58):
        #print(i)
        if i % 9 > 0:
            n = 3 + 2*i
            tables_1d_1h = tables.split('\"')[n]   #第一天，第一小时,2n+3
            if len(tables_1d_1h) >=7:
                temp = tables_1d_1h.split(',')[3]
                temp_int = int(re.findall(r"\d+",temp)[0])
                rain = tables_1d_1h.split(',')[2]
                
                pre_date = tables_1d_1h.split(',')[0]
                pred_day = re.findall(r"\d+",pre_date)[0]
                pred_hour = re.findall(r"\d+",pre_date)[1]
                get_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                pred_time = ('%s%s' %(get_time[:8],pred_day))
                ALL_DATA.append({'get_date':get_time[:10],
                                    'get_hour':get_time[11:13],
                                    'pred_date':pred_time,
                                    'pred_hour':pred_hour,
                                    'temperature': temp_int,     
                                    'rain': rain,
                                    'rain_proba':np.nan,
                                    'city_name':city_name
                                   })
                city_weather = pd.DataFrame(ALL_DATA, columns=['get_date','get_hour','pred_date','pred_hour','temperature','rain','rain_proba','city_name'])
        else:
            i += 1
    city_weather.index = city_weather.pred_date + '-' + city_weather.pred_hour
    #city_weather = city_weather[city_weather.city_name != '香格里拉']
    city_weather.sort_index()
    return city_weather
city_name_re = pd.DataFrame({'city_name':['红河市','大理市','西双版纳市','文山市','楚雄市','德宏市','怒江市','迪庆市','凉山市','黔西南市','黔东南市','黔南市','铜仁市','毕节市','成都市','昆明市','曲靖市','丽江市','保山市','普洱市','玉溪市','昭通市','临沧市','南充市','绵阳市','德阳市','遂宁市','达州市','广元市','广安市','巴中市','乐山市','宜宾市'
                                         ,'眉山市','泸州市','内江市','资阳市','自贡市','雅安市','攀枝花市','遵义市','贵阳市','安顺市','六盘水市'],
                            'city_new':['红河州','大理州','西双版纳州','文山州','楚雄州','德宏州','怒江州','迪庆州','凉山州','黔西南州','黔东南州','黔南州','铜仁地区','毕节地区','成都市','昆明市','曲靖市','丽江市','保山市','普洱市','玉溪市','昭通市','临沧市','南充市','绵阳市','德阳市','遂宁市','达州市','广元市','广安市','巴中市','乐山市','宜宾市'
                                        ,'眉山市','泸州市','内江市','资阳市','自贡市','雅安市','攀枝花市','遵义市','贵阳市','安顺市','六盘水市']})

######################################################################
#定义分割降雨的函数get_intensity_data
def get_intensity_data(filed):
    if filed == '暴雨':
        return 71.4
    elif filed == '大雨':
        return 33.3
    elif filed == '中雨':
        return 14.6
    elif filed == '小雨':
        return 1.5
    elif filed == '阵雨':
        return 1.6 
    elif filed == '雷阵雨':
        return 1.9   
    else:
        return 0

######################################################################
def get_wc_forecast_weather():
    urls = []
    city_weather_all = pd.DataFrame()
    #四川城市url
    for i in range(1,22):
        if i < 10:
            urls.append('http://www.weather.com.cn/weather/101270{}01.shtml'.format(i))
        else:
            urls.append('http://www.weather.com.cn/weather/10127{}01.shtml'.format(i))
    #贵州url--http://www.weather.com.cn/weather/101260101.shtml
    for i in range(1,10):
            urls.append('http://www.weather.com.cn/weather/101260{}01.shtml'.format(i))
    #云南--http://www.weather.com.cn/weather/101290101.shtml；http://www.weather.com.cn/weather/101291601.shtml
    for i in range(1,17):
        if i != 13:
            if i < 10:
                urls.append('http://www.weather.com.cn/weather/101290{}01.shtml'.format(i))
            else:
                urls.append('http://www.weather.com.cn/weather/10129{}01.shtml'.format(i))
    for url in urls:
        city_weather = parse_page(url)
        # print(city_weather.iat[len(city_weather.city_name)-1,6])
        city_weather_all = city_weather_all.append(city_weather)
        ##0620增加列 soure
    city_weather_all['source'] = 'weather_china'
    city_weather_all['get_date_hour']  = city_weather_all.get_date +  '-' + city_weather_all.get_hour
    city_weather_all['pred_date_hour']  = city_weather_all.pred_date +  '-' + city_weather_all.pred_hour
    city_weather_all_2 = city_weather_all[city_weather_all.index >= city_weather_all.get_date_hour]
    
    city_weather_all_2['get_date_2d'] = (pd.to_datetime(city_weather_all_2.get_date) + dt.timedelta(days=2)).apply(lambda x:x.strftime("%Y-%m-%d"))  +  '-' + city_weather_all_2.get_hour
    city_weather_all_2 = city_weather_all_2[city_weather_all_2.get_date_2d >= city_weather_all_2.pred_date_hour]
    
    city_weather_all_2 = pd.merge(city_weather_all_2,city_name_re,how='inner',on='city_name')
    city_weather_all_2 = city_weather_all_2[['source','get_date','get_hour','pred_date','pred_hour','temperature','rain','rain_proba','city_new']]   #.reset_index(drop=True)
    city_weather_all_2.columns = ['source','get_date','get_hour','pred_date','pred_hour','temperature','rain','rain_proba','city_name']
    city_weather_all_2['rain'] = city_weather_all_2['rain'].apply(lambda x: get_intensity_data(x))
    return city_weather_all_2


##############################################################################################################################
# 1.4 DARK_SKY
##############################################################################################################################

##############################################################################################################################
#整数转时间函数
def intstr_2_time(intstr):
    timeArray = time.localtime(intstr)
    Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return Time

######################################################################
#单个城市的天气数据提取
def get_dark_sky_48h_weather(latitude, longitude):
    #获取数据
    url=f'https://api.darksky.net/forecast/328a25efc2600052bab52217c7bd9326/{latitude},{longitude}?exclude=minutely,currently,daily,alerts,flags'
    data = json.loads(requests.get(url=url).text)
    data =pd.DataFrame(data['hourly']['data'])
    #时间
    data['time'] = data['time'].apply(lambda x: intstr_2_time(x))
    get_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #列信息
    data['source'] = 'dark_sky'
    data['get_date'] = get_time[:10]
    data['get_hour'] = get_time[11:13]
    data['pred_date'] = data['time'].str[:10]
    data['pred_hour'] = data['time'].str[11:13]
    data['rain'] = data['precipIntensity']*25.4
    data['rain_proba'] = data['precipProbability']
    data['temperature'] = np.round((data['temperature']-32)/1.8, 2)
    #保留对应数据
    data = data[['source','get_date','get_hour','pred_date','pred_hour','rain','rain_proba','temperature']]
    return data

######################################################################
#城市天气数据汇总
def get_dark_sky_forecast_weather(locations):
    city_list = list(locations.keys())
    weather = pd.DataFrame()
    for city_name in city_list:
        latitude=locations[city_name]['latitude']
        longitude=locations[city_name]['longitude']
        city_weather = get_dark_sky_48h_weather(latitude, longitude)
        #城市的名称
        city_weather['city_name'] = city_name
        weather = weather.append(city_weather)
    return weather
##############################################################################################################################
#汇总所有天气数据
def get_forecast_weather_data():
    #开始时间
    starttime = dt.datetime.now()
    #准备空数据框存储数据
    weather_forecast = pd.DataFrame()
    ######################################################################
    #ACCU部分
    ######################################################################
    #川北+成都
    try:
        # API_1 = 'AAmEHgLDbG1Ufy343DIfYNn0QnkmWwR6'                    #测试用-GAP
        # API_1 = 'SoTPoZEXFgtGH1AomhWyXyine46kCijB'                    #测试用-GAP
        # LOCATIONS_1 = {'成都市':106774}                              #测试用
        API_1 = 'WGajM6FNuDlFOcdtlbwQBn0pFuhACVmB'                  #yys
        LOCATIONS_1 = {'成都市':106774,'南充市':60980,'绵阳市':60974,'德阳市':60971,'遂宁市':60976,'达州市':2333431,'广元市':60970,'广安市':61034,'巴中市':61041}
        accu_sw_weather_1 = get_accu_forecast_weather(API_1, LOCATIONS_1)
        weather_forecast=weather_forecast.append(accu_sw_weather_1)
    except:
        print('ACCU信息：ERROR-CD/CB')
    #川南
    try:
        API_2 = 'HWn5AgD34BcQAlpe1XKAyTh1qNDo2hcL'                  #lsh
        LOCATIONS_2 = {'乐山市':60972,'宜宾市':60981,'眉山市':61051,'泸州市':60973,'内江市':60975,'资阳市':60969,'自贡市':106775,'雅安市':60968,'凉山州':2333449,'攀枝花市':61035,'甘孜州':80413}
        accu_sw_weather_2 = get_accu_forecast_weather(API_2, LOCATIONS_2)
        weather_forecast=weather_forecast.append(accu_sw_weather_2)
    except:
        print('ACCU信息：ERROR-CN')
    #贵州
    try:
        API_3 = 'sLCcyGEWJDMXkfHV0GMxLPDzyFB3dqKW'                   #hz
        LOCATIONS_3 = {'遵义市':58497,'贵阳市':102273,'黔西南州':2332728,'安顺市':58492,'黔东南州':2332712,'黔南州':2332723,'铜仁地区':58491,'毕节地区':58493,'六盘水市':102274}
        accu_sw_weather_3 = get_accu_forecast_weather(API_3, LOCATIONS_3)
        weather_forecast=weather_forecast.append(accu_sw_weather_3)
    except:
        print('ACCU信息：ERROR-GZ')
    #云南
    try:
        API_4 = 'Vo1SFMvpWHxSDVvHOrknBejGdU38gJry'                   #hzx
        LOCATIONS_4 = {'昆明市':106812,'曲靖市':61412,'丽江市':2333576,'红河州':61439,'大理州':61417,'西双版纳州':2333601,'保山市':61476,'普洱市':2333590,'玉溪市':61488,'文山州':2333595,'楚雄州':61409,'昭通市':61420,'德宏州':2333559,'临沧市':61475,'怒江州':2595163}
        accu_sw_weather_4 = get_accu_forecast_weather(API_4, LOCATIONS_4)
        weather_forecast=weather_forecast.append(accu_sw_weather_4)
    except:
        print('ACCU信息：ERROR-YN')
    print('DONE 1/4 : ACCU信息')
    #结束时间
    endtime_1 = dt.datetime.now()
    #运行时间
    print('ACCU信息采集时间：',(endtime_1 - starttime).seconds, '秒')

    ######################################################################
    #CAIYUN
    ######################################################################
    #彩云数据的生成时间在小时的前几分钟，更新时间应设置在15分钟以后
    try:
        get_time = (dt.datetime.now()+dt.timedelta(hours=-1)).strftime("%Y-%m-%d %H:%M:%S")
        ymdh = get_time[0:10]+'-'+get_time[11:13]
        data = get_caiyun_source(ymdh)

        caiyun_sw_weather = get_caiyun_forecast_weather(data)

        weather_forecast=weather_forecast.append(caiyun_sw_weather)
    except:
        print('彩云信息：ERROR')
    print('DONE 2/4 : 彩云信息')
    #结束时间
    endtime_2 = dt.datetime.now()
    #运行时间
    print('彩云信息采集时间：',(endtime_2 - endtime_1).seconds, '秒')
    ######################################################################
    #DARK_SKY
    ######################################################################
    try:
        # LOCATIONS_LL = {'成都市': {'latitude':30.572269,'longitude':104.066541}}                 #测试用
        LOCATIONS_LL = {'成都市': {'latitude':30.572269,'longitude':104.066541},'昆明市': {'latitude':24.880095,'longitude':102.832892},'曲靖市': {'latitude':25.49,'longitude':103.796167},'丽江市': {'latitude':26.855047,'longitude':100.227751},'红河州': {'latitude':23.36313,'longitude':103.374799},'大理州': {'latitude':25.606486,'longitude':100.267638},'西双版纳州': {'latitude':22.007351,'longitude':100.797777},'保山市': {'latitude':25.112046,'longitude':99.161761},'普洱市': {'latitude':22.825066,'longitude':100.966512},'玉溪市': {'latitude':24.352036,'longitude':102.546543},'文山州': {'latitude':23.400733,'longitude':104.216248},'楚雄州': {'latitude':25.045532,'longitude':101.528069},'昭通市': {'latitude':27.338257,'longitude':103.717465},'德宏州': {'latitude':24.433353,'longitude':98.584895},'临沧市': {'latitude':23.877573,'longitude':100.079583},'怒江州': {'latitude':25.817556,'longitude':98.856601},'迪庆州': {'latitude':27.818757,'longitude':99.702254},'南充市': {'latitude':30.837793,'longitude':106.110698},'绵阳市': {'latitude':31.46745,'longitude':104.679114},'德阳市': {'latitude':31.126856,'longitude':104.397894},'遂宁市': {'latitude':30.532847,'longitude':105.592898},'达州市': {'latitude':31.209572,'longitude':107.468023},'广元市': {'latitude':32.435435,'longitude':105.843357},'广安市': {'latitude':30.455962,'longitude':106.633212},'巴中市': {'latitude':31.867903,'longitude':106.747478},'阿坝州': {'latitude':31.899413,'longitude':102.224653},'乐山市': {'latitude':29.552106,'longitude':103.765568},'宜宾市': {'latitude':28.751769,'longitude':104.643215},'眉山市': {'latitude':30.07544,'longitude':103.848538},'泸州市': {'latitude':28.871811,'longitude':105.442258},'内江市': {'latitude':29.580229,'longitude':105.058433},'资阳市': {'latitude':30.128901,'longitude':104.627636},'自贡市': {'latitude':29.33903,'longitude':104.778442},'雅安市': {'latitude':29.980537,'longitude':103.013261},'凉山州': {'latitude':27.881611,'longitude':102.267335},'攀枝花市': {'latitude':26.582347,'longitude':101.718637},'甘孜州': {'latitude':30.04952,'longitude':101.962311},'遵义市': {'latitude':27.725654,'longitude':106.927389},'贵阳市': {'latitude':26.647661,'longitude':106.630154},'黔西南州': {'latitude':25.087825,'longitude':104.906397},'安顺市': {'latitude':26.253072,'longitude':105.947594},'黔东南州': {'latitude':26.583442,'longitude':107.982859},'黔南州': {'latitude':26.254092,'longitude':107.522098},'铜仁地区': {'latitude':27.731515,'longitude':109.189598},'毕节地区': {'latitude':27.283955,'longitude':105.291644},'六盘水市': {'latitude':26.592666,'longitude':104.830359}}
        ds_sw_weather = get_dark_sky_forecast_weather(LOCATIONS_LL)
        weather_forecast=weather_forecast.append(ds_sw_weather)
    except:
        print('DARK_SKY信息：ERROR')

    print('DONE 3/4 : Dark_Sky信息')
    #结束时间
    endtime_3 = dt.datetime.now()
    #运行时间
    print('Dark_Sky信息采集时间：',(endtime_3 - endtime_2).seconds, '秒')

    ######################################################################
    #WEAHTHER_CHINA
    ######################################################################
    try:
        wc_sw_weather = get_wc_forecast_weather()
        wc_sw_weather['rain'] = wc_sw_weather['rain'].astype('float')
        wc_sw_weather['temperature'] = wc_sw_weather['temperature'].astype('float')
    
        #最大最小转换
        weather_forecast['rain'] = weather_forecast['rain'].astype('float')
        weather_forecast['temperature'] = weather_forecast['temperature'].astype('float')
        #最大的降雨值
        max_rain = weather_forecast['rain'].max()
        max_wc_rain = wc_sw_weather['rain'].max()
    
        if max_wc_rain > max_rain:
            try:
                ration = max_rain/max_wc_rain
                wc_sw_weather['rain'] = wc_sw_weather['rain']*ration
                weather_forecast=weather_forecast.append(wc_sw_weather)
            except:
                weather_forecast=weather_forecast.append(wc_sw_weather)
        else:
            weather_forecast=weather_forecast.append(wc_sw_weather)
        print('DONE 4/4 : 中国天气网信息')
    except:
        print('weather_china信息：ERROR')    
    #结束时间
    endtime_4 = dt.datetime.now()
    #运行时间
    print('中国天气网信息采集时间：',(endtime_4 - endtime_3).seconds, '秒')
    ######################################################################
    #去重
    weather_forecast.drop_duplicates(inplace = True)
    #将降雨概率调整为0~100
    weather_forecast['rain_proba']=weather_forecast['rain_proba']*100
    #数据格式调整
    weather_forecast['pred_hour']=weather_forecast['pred_hour'].astype(int)
    weather_forecast['rain'] = weather_forecast['rain'].astype('float64')
    #打印信息
    print('\n天气预测信息采集：DONE')
    #结束时间
    endtime = dt.datetime.now()
    #运行时间
    print('信息采集时间：',(endtime - starttime).seconds, '秒')
    return weather_forecast


##############################################################################################################################
# 预警信息
##############################################################################################################################
#峰期判断函数
def peak(hour):
    '''
    区分时间所属的峰期
    '''
    if hour== 7 or hour==8 or hour==9:
        return '早峰'
    elif hour== 12 or hour==13 or hour==14:
        return '午峰'
    elif hour== 17 or hour==18:
        return '晚峰'
    elif hour== 19 or hour==20 or hour==21 or hour==22 or hour==23:
        return '夜峰'
    elif hour== 0 or hour==1 or hour==2 or hour== 3 or hour==4 or hour==5 or hour==6:
        return '凌晨'
    elif hour== 10 or hour==11:
        return '早平峰'
    elif hour== 15 or hour==16:
        return '下平峰'
    else:
        return '非正常小时'

#分数据源汇总数据
def gather_data(data, source):
    '''
    按不同来源汇总天气预报数据
    '''
    data_source = data[data['source']==source]
    data_source = data_source[['city_name','pred_date', 'pred_hour','rain','rain_proba']]
    data_source.rename(columns={'rain':'{}_rain'.format(source), 'rain_proba':'{}_rain_proba'.format(source)}, inplace=True)
    data_source.fillna(0, inplace=True)
    return data_source

#生成两个序列中对应数据的最大值及对应值
def max_corresponding_value(seq1, seq2):
    '''
    返回seq1中最大值，在seq2对应位置的值
    '''
    max_value=max(seq1)
    for x, y in zip(seq1, seq2):
        if x == max_value:
            return y
            break
        else:
            continue

#策略建议
def strategy(high_proba_num, rain_proba):
    '''
    根据降雨概率和降雨数目，给出策略建议
    '''
    if high_proba_num>=2:
        return '策略_GO'
    elif high_proba_num >=1 and rain_proba>=70:
        return '策略_GO'
    elif high_proba_num >=1 and rain_proba>=60:
        return '策略_自决_HP'
    elif high_proba_num >=1:
        return '策略_自决'
    else:
        return '策略_Hold'

#匹配城市群
def city_group(city_name):
    city_dict={
        '成都市': '成都',
        '昆明市': '昆明',
        '曲靖市': '云南潜力','丽江市': '云南潜力','红河州': '云南潜力','大理州': '云南潜力','西双版纳州': '云南潜力','保山市': '云南潜力','普洱市': '云南潜力','玉溪市': '云南潜力','文山州': '云南潜力','楚雄州': '云南潜力','昭通市': '云南潜力','德宏州': '云南潜力','临沧市': '云南潜力','怒江州': '云南潜力','迪庆州': '云南潜力',
        '南充市': '川北','绵阳市': '川北','德阳市': '川北','遂宁市': '川北','达州市': '川北','广元市': '川北','广安市': '川北','巴中市': '川北','阿坝州': '川北','乐山市': '川南','宜宾市': '川南','眉山市': '川南','泸州市': '川南','内江市': '川南','资阳市': '川南','自贡市': '川南','雅安市': '川南','凉山州': '川南','攀枝花市': '川南','甘孜州': '川南',
        '遵义市': '贵州','贵阳市': '贵州','黔西南州': '贵州','安顺市': '贵州','黔东南州': '贵州','黔南州': '贵州','铜仁地区': '贵州','毕节地区': '贵州','六盘水市': '贵州'
    }
    return city_dict[city_name]

#降雨级别函数
def get_level(filed):
    if filed < 0.1:
        return '无雨'
    elif filed < 5:
        return '小雨'
    elif filed < 15:
        return '中雨'
    elif filed < 30:
        return '大雨'
    else:
        return '暴雨'

def render_mpl_table(data, pic_name, col_width=3.0, row_height=0.625, font_size=15,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    '''
    将DF转换为图片
    '''
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    plt.savefig("{}.jpg".format(pic_name))



#预警信息函数
def weather_alarm_data(data):
    #构建峰期列
    data['peak']=data['pred_hour'].map(peak)
    #数据汇总
    data_mask = data.copy()
    data_mask = data_mask[['city_name','pred_date', 'pred_hour','peak']]
    data_mask.drop_duplicates(['city_name','pred_date', 'pred_hour'], inplace=True)
    for source in ['accu','caiyun','dark_sky','weather_china']:
        data_source=gather_data(data, source)
        #数据合并
        data_mask = pd.merge(data_mask, data_source, how='left', on=['city_name','pred_date', 'pred_hour'])
    #填充
    data_mask.fillna(0, inplace=True)

    #获取最大降雨概率
    data_mask['max_rain_proba'] = data_mask[['accu_rain_proba','caiyun_rain_proba','dark_sky_rain_proba','weather_china_rain_proba']].max(axis=1)

    #合并降雨和概率的数据
    data_mask['rain_list'] = data_mask[['accu_rain','caiyun_rain','dark_sky_rain','weather_china_rain']].values.tolist()
    data_mask['rain_proba_list'] = data_mask[['accu_rain_proba','caiyun_rain_proba','dark_sky_rain_proba','weather_china_rain_proba']].values.tolist()

    #超过降雨概率阈值的数量+降雨数量
    data_mask['high_proba_num']= np.ceil((data_mask['accu_rain_proba']-50)/100)+np.ceil((data_mask['caiyun_rain_proba']-50)/100)+np.ceil((data_mask['dark_sky_rain_proba']-50)/100)+np.ceil((data_mask['weather_china_rain_proba']-50)/100)
    data_mask['drop_rain_num']=np.ceil((data_mask['accu_rain']-0.1)/10000)+np.ceil((data_mask['caiyun_rain']-0.1)/10000)+np.ceil((data_mask['dark_sky_rain']-0.1)/10000)+np.ceil((data_mask['weather_china_rain']-0.1)/10000)
    #获取最大降雨概率下的降雨
    data_mask['max_rain_proba_cor_rain']=data_mask.apply(lambda x: max_corresponding_value(x['rain_proba_list'],x['rain_list']),axis=1)
    
    #修改列名
    data_mask.rename(columns={'max_rain_proba_cor_rain':'rain','max_rain_proba':'rain_proba'},inplace=True)
    #保留有降雨的数据
    data_mask = data_mask[data_mask['drop_rain_num']>=1]
    
    #保留对应的数据
    list_remain_alarm=['city_name','pred_date', 'pred_hour','rain','rain_proba','high_proba_num', 'drop_rain_num','peak']
    data_mask = data_mask[list_remain_alarm]

    #生成策略建议
    data_mask['strategy_advice']=data_mask.apply(lambda x : strategy(x['high_proba_num'], x['rain_proba']), axis=1)

    #保留对应数据
    data_mask = data_mask[['city_name','pred_date','pred_hour','peak', 'rain','rain_proba','strategy_advice']]

    #平均降雨及平均降雨概率
    group0 = pd.DataFrame(data_mask.groupby(['city_name','pred_date','peak','strategy_advice'])['rain','rain_proba'].mean())
    group0.reset_index(inplace=True)

    #将小时数据汇集成1行
    group1 = pd.DataFrame(data_mask.groupby(['city_name','pred_date','peak','strategy_advice'])['pred_hour'].min())
    group1.reset_index(inplace=True)
    group1.rename(columns={'pred_hour':'min_pred_hour'},inplace=True)
    
    group2 = pd.DataFrame(data_mask.groupby(['city_name','pred_date','peak','strategy_advice'])['pred_hour'].max())
    group2.reset_index(inplace=True)
    group2.rename(columns={'pred_hour':'max_pred_hour'},inplace=True)

    peak_alarm_data=data_mask.copy()
    peak_alarm_data = peak_alarm_data[['city_name','pred_date','peak','strategy_advice']]
    peak_alarm_data.drop_duplicates(inplace=True)
    
    #数据合并
    peak_alarm_data = pd.merge(peak_alarm_data, group0, how='left', on=['city_name','pred_date','peak','strategy_advice'])
    peak_alarm_data = pd.merge(peak_alarm_data, group1, how='left', on=['city_name','pred_date','peak','strategy_advice'])
    peak_alarm_data = pd.merge(peak_alarm_data, group2, how='left', on=['city_name','pred_date','peak','strategy_advice'])
    
    #最大最小判断
    peak_alarm_data['min_max_compare']=peak_alarm_data['max_pred_hour']-peak_alarm_data['min_pred_hour']
    
    #时间区间
    peak_alarm_data['min_pred_hour']=peak_alarm_data['min_pred_hour'].astype('str')
    peak_alarm_data['max_pred_hour']=peak_alarm_data['max_pred_hour'].astype('str')

    #生成时间跨度
    peak_alarm_data['hour2hour']=peak_alarm_data['min_pred_hour'].str.cat(peak_alarm_data['max_pred_hour'],sep='-')
    peak_alarm_data['period']=np.where(peak_alarm_data['min_max_compare']>=1, peak_alarm_data['hour2hour'], peak_alarm_data['min_pred_hour'])
    
    #重新排序
    peak_alarm_data.sort_values(['strategy_advice'],inplace=True)
    
    #保留数据
    peak_alarm_data=peak_alarm_data[['city_name','pred_date','period','rain','rain_proba','strategy_advice']]
    
    peak_alarm_data.reset_index(drop=True, inplace=True)

    #构建城市群列
    peak_alarm_data['city_group']=peak_alarm_data['city_name'].map(city_group)

    #调整数据输出
    list_out=['city_group','city_name','pred_date','period','rain','rain_proba','strategy_advice']
    peak_alarm_data=peak_alarm_data[list_out]

    peak_alarm_data['rain']=peak_alarm_data['rain'].map(get_level)

    #剔除无雨数据
    peak_alarm_data=peak_alarm_data[peak_alarm_data['rain']!='无雨']
    
    #概率列保留两位小数
    peak_alarm_data['rain_proba']=np.round(peak_alarm_data['rain_proba'],2)
    
    # 数据排序
    peak_alarm_data.sort_values(['city_group','city_name','pred_date','period'], inplace=True)
    peak_alarm_data.reset_index(drop=True, inplace=True)

    #去除Hold数据
    peak_alarm_data=peak_alarm_data[peak_alarm_data['strategy_advice']!='策略_Hold']

    #列名更改为汉字
    peak_alarm_data.rename(columns={'city_group':'城市群','city_name':'城市','pred_date':'预测日期','period':'时间','rain':'降雨级别','rain_proba':'降水概率','strategy_advice':'策略建议'}, inplace=True)
    return peak_alarm_data

#日期+小时
def datehour(x):
    dh=x['pred_date']+dt.timedelta(hours=x['pred_hour'])
    return dh 

#可视化
def create_detail_graph(data):
    #数据调整
    list_remain =['city_name', 'get_date', 'get_hour', 'pred_date', 'pred_hour', 'rain', 'rain_proba','source', 'temperature']#增加新列rain_proba
    weather=data[list_remain]
    weather['pred_date']=pd.to_datetime(weather['pred_date'])
    #时间列
    weather['datehour']=weather.apply(datehour,axis=1)
    #城市列表，筛选框
    input_dropdown = alt.binding_select(options=[
        '成都市',
        '昆明市','曲靖市','丽江市','红河州','大理州','西双版纳州','保山市','普洱市','玉溪市','文山州','楚雄州','昭通市','德宏州','临沧市','怒江州','迪庆州',
        '南充市','绵阳市','德阳市','遂宁市','达州市','广元市','广安市','巴中市',
        '乐山市','宜宾市','眉山市','泸州市','内江市','资阳市','自贡市','雅安市','凉山州','攀枝花市',
        '遵义市','贵阳市','黔西南州','安顺市','黔东南州','黔南州','铜仁地区','毕节地区','六盘水市'
        ])
    selection = alt.selection_single(fields=['city_name'], bind=input_dropdown, name='*')
    color = alt.condition(selection,
        alt.Color('source:N', legend=None),
        alt.value('lightgray'))
    #小雨线
    weather['level_xy']=0.1
    
    base = alt.Chart(weather).properties(width=1000,
        height=200)

    line = base.mark_line().encode(
        x='datehour:T',
        y=alt.Y('rain',axis=alt.Axis(title='rain    mmh')),
        color='source:N',
        tooltip='pred_hour:Q'
    ).add_selection(
        selection
    ).transform_filter(
        selection
    )

    rule = base.mark_rule().encode(
        y=alt.Y('mean(level_xy):Q',axis=alt.Axis(title=None)),
        size=alt.SizeValue(2)
    )
    
    a=line+rule

    b=alt.Chart(weather).mark_line().encode(
        x='datehour:T',
        y=alt.Y('rain_proba:Q',axis=alt.Axis(title='rain_proba     %'),
            scale=alt.Scale(domain=(0,100))),
        color='source:N',
        tooltip='pred_hour:Q'
    ).add_selection(
        selection
    ).transform_filter(
        selection
    ).properties(
        width=1000,
        height=200
    ) 
    
    c=alt.Chart(weather).mark_line().encode(
        x='datehour:T',
        y = alt.Y('temperature',axis=alt.Axis(title='temperature    C')),
        color='source:N',
        tooltip='pred_hour:Q'
    ).add_selection(
        selection
    ).transform_filter(
        selection
    ).properties(
        width=1000,
        height=200
    )
    #保存文件
    (a&b&c).save('1.html')
########################################################################################################################
#信息上传
########################################################################################################################
#数据上传
def postdata(url, data, files, headers):
    r=requests.post(url=url,data=data,files=files,headers=headers)

#通知城市运营负责人
def at_person(df, type='peak'):
    '''
    根据预警信息，@对应的城市负责人
    '''
    len1 = len(df)
    len2 = len(df[(df['策略建议']=='策略_GO') | (df['策略建议']=='策略_自决_HP')])
    atmap={
        '川北':'cuizhe',
        '川南':'tanluning',
        '贵州':'taoxi @chengzhanghao',
        '昆明':'walisi @shanzudi',
        '云南潜力':'xiayuezhu',
        '成都':'huangzongze @leiyayun @florawuzeng'
    }
    city_name=df['城市'].drop_duplicates().values.tolist()

    # 峰期预警情况        
    if type == 'peak':
        #有预警信息时
        if len1>0 and len2>0:
            at=df[(df['策略建议']=='策略_GO') | (df['策略建议']=='策略_自决_HP')]
            at=at['城市群'].drop_duplicates().values.tolist()
            # 构建@人员信息
            content=''
            for i in at:
                tem=atmap[i]
                atperson='@'+tem
                content=content+' '+atperson
            content = {
                "text": (content+' 您负责的城市降雨概率较大，请提前做好准备!')
            }
        #有预警信息，但降雨概率不高
        elif len1>0:
            content = {
                 "text": (' 请持续关注重点城市的天气信息!')
            }
        #无预警信息
        else:
            content = {
                "text": (' 暂无峰期降雨预警，请持续关注重点城市的天气信息!')
            }
    #平峰预警情况
    else:
        #有平峰预警信息
        if len1 > 0:
            at = df.copy()
            at=at['城市群'].drop_duplicates().values.tolist()
            # 构建@人员信息
            content=''
            for i in at:
                tem=atmap[i]
                atperson='@'+tem
                content=content+' '+atperson
            content = {
                "text": (content+' 您负责的城市平峰期间有大降雨，请注意!')
            }
    return content

def upload_data(today, peak_alarm_volumn, none_peak_alarm_volumn):
    #上传参数
    url='http://agility.intra.xiaojukeji.com/file/upload'
    headers={'secretkey':'AZ1ghisG0'}
    requests.adapters.DEFAULT_RETRIES = 20

    #详细降雨数据上传
    files ={'file':open('1.html')}
    data={'key':f'weatherdata{today}.html','namespace':'sw_weather_fore','pubArea':'hxy02'}
    #上传数据1
    postdata(url, data, files, headers)

    if peak_alarm_volumn == 1:
        #图片上传：
        files = {'file': open('peak_alarm_image.jpg', 'rb')}
        data={'key':f'weatherdata{today}.jpg','namespace':'sw_weather_fore','pubArea':'hxy02'}
        #上传数据2
        postdata(url, data, files, headers)
    else:
        #图片上传-无预警图片：
        files = {'file': open('no_alarm_image.jpg', 'rb')}
        data={'key':f'weatherdata_no_alarm{today}.jpg','namespace':'sw_weather_fore','pubArea':'hxy02'}
        #上传数据2
        postdata(url, data, files, headers)
    
    if none_peak_alarm_volumn == 1:
        #图片上传-平峰预警图片：
        files = {'file': open('none_peak_alarm_image.jpg', 'rb')}
        data={'key':f'weatherdata_none_peak{today}.jpg','namespace':'sw_weather_fore','pubArea':'hxy02'}
        #上传数据2
        postdata(url, data, files, headers)       

#峰期信息
def post_peak_content(today, peak_alarm_volumn):
    #峰期预警信息
    if peak_alarm_volumn ==1:
        #上载信息-第一段话部分：
        link_url=f'''http://img-hxy021.didistatic.com/static/sw_weather_fore/weatherdata{today}.html'''   
        content = {
            "text": f'''**近48小时天气预报** \n爬虫时间:{today}''',
            "markdown": 'true',
            "attachments": [
                {
                "title": '''_点击此处可查看全量城市分时温度降雨数据_''',
                "text":"峰期降雨预警及策略建议",
                "url": link_url,
                "images": [
                    {
                    "url": f"http://dpubstatic.udache.com/static/sw_weather_fore/weatherdata{today}.jpg"
                    }
                    ]
                }
            ]
        }
        
        #上载信息-第二段话-需要设置重点城市与城市负责人
        content1=at_person(peak_alarm_data, 'peak')
        #信息上载
        f=requests.post(url, json=content)
        f=requests.post(url, json=content1)
    else:
        #上载信息-第一段话部分：
        link_url=f'''http://img-hxy021.didistatic.com/static/sw_weather_fore/weatherdata{today}.html'''   
        content = {
            "text": f'''**近48小时天气预报** \n爬虫时间:{today}''',
            "markdown": 'true',
            "attachments": [
                {
                "title": '''_点击此处可查看全量城市分时温度降雨数据_''',
                "text":"暂无峰期预警数据，请持续关注天气",
                "url": link_url,
                "images": [
                    {
                    "url": f"http://dpubstatic.udache.com/static/sw_weather_fore/weatherdata_no_alarm{today}.jpg"
                    }
                    ]
                }
            ]
        }
        #信息上载
        f=requests.post(url, json=content)

#平峰信息
def post_none_peak_content(today, none_peak_alarm_volumn):
    #平峰预警信息
    if none_peak_alarm_volumn ==1:
        #上载信息-第一段话部分： 
        content2 = {
            "attachments": [
                {
                "text":"平峰大雨预警",
                "images": [
                    {
                    "url": f"http://dpubstatic.udache.com/static/sw_weather_fore/weatherdata_none_peak{today}.jpg"
                    }
                    ]
                }
            ]
        }
        
        #上载信息-第二段话-需要设置重点城市与城市负责人
        content3=at_person(none_peak_alarm_data, 'none_peak')    
        
        #信息上载
        f=requests.post(url, json=content2)
        f=requests.post(url, json=content3)
########################################################################################################################
########################################################################################################################
#天气预警
if __name__ == "__main__":
    ####################################################################################################################
    #PART ONE 天气信息采集
    ####################################################################################################################
    #获取天气数据
    weather_forecast = get_forecast_weather_data()

    #数据导出
    now_string = dt.datetime.now().strftime('%Y-%m-%d-%H') #当前时刻
    weather_forecast.to_csv('weather_forecast_{}.csv'.format(now_string), encoding='gbk', index=False)
    print('\n天气预测信息导出：DONE')
    print('\n#####################################################################')
    #时间暂停
    time.sleep(10)
    ####################################################################################################################
    #PART TWO 天气预警信息
    ####################################################################################################################
    #构建峰期列
    weather_forecast['peak']=weather_forecast['pred_hour'].map(peak)

    #峰期预警信息
    peak_weather_data = weather_forecast[(weather_forecast['peak']=='早峰') | (weather_forecast['peak']=='午峰') | (weather_forecast['peak']=='晚峰') | (weather_forecast['peak']=='夜峰')]
    
    peak_alarm_data = weather_alarm_data(peak_weather_data)
    if len(peak_alarm_data) > 0:
        #预警信息保存
        peak_alarm_data.to_csv('peak_alarm_data_{}.csv'.format(now_string), encoding='gbk', index=False)
        #生成图片
        render_mpl_table(peak_alarm_data, pic_name='peak_alarm_image', header_columns=0, col_width=2.0)
        #峰期标识
        peak_alarm_volumn = 1
    else:
        peak_alarm_volumn = 0
        print('无峰期预警信息！')

    #保留非峰期数据
    none_peak_weather_data = weather_forecast[(weather_forecast['peak']=='凌晨') | (weather_forecast['peak']=='上平峰') | (weather_forecast['peak']=='下平峰')]
    none_peak_alarm_data = weather_alarm_data(none_peak_weather_data)
    #大雨及以上数据保留
    none_peak_alarm_data= none_peak_alarm_data[(none_peak_alarm_data['降雨级别']=='大雨') | (none_peak_alarm_data['降雨级别']=='暴雨')]
    #降雨概率大于50
    none_peak_alarm_data= none_peak_alarm_data[none_peak_alarm_data['降水概率'] >= 50]
    #将策略建议修改
    none_peak_alarm_data['策略建议']='Heavy Rain'
    
    if len(none_peak_alarm_data) > 0:
        #预警信息保存
        none_peak_alarm_data.to_csv('none_peak_data_{}.csv'.format(now_string), encoding='gbk', index=False)
        #生成图片
        render_mpl_table(none_peak_alarm_data, pic_name='none_peak_alarm_image', header_columns=0, col_width=2.0)
        #非峰期标识
        none_peak_alarm_volumn = 1
        print('\n峰期预警图片生成：DONE')
        print('\n#####################################################################')
        #时间暂停
        time.sleep(10)
    else:
        none_peak_alarm_volumn = 0
        print('无平峰预警信息！')
        print('\n#####################################################################')
    
    #生成HTML详细信息
    create_detail_graph(weather_forecast)
    print('\n详情HTML文件生成：DONE')
    print('\n#####################################################################')
    #时间暂停
    time.sleep(10)
    ######################################################################
    #PART THREE 信息输出
    ######################################################################
    #信息上传
    today = dt.datetime.now().strftime("%Y-%m-%d-%H-%M")
    upload_data(today, peak_alarm_volumn, none_peak_alarm_volumn)
    print('\n天气预测文件上传：DONE')
    print('\n#####################################################################')
    #时间暂停
    time.sleep(10)

    #测试链接
    url='https://im-dichat.xiaojukeji.com/api/hooks/incoming/ad7effb0-926c-4ff8-a08d-0ad30b5ad0a8'
    #正式发送
    # url='https://im-dichat.xiaojukeji.com/api/hooks/incoming/31759594-0a15-4388-8042-136a05a8cc7e'
    
    #峰期信息输出
    post_peak_content(today, peak_alarm_volumn)
    #平峰信息输出
    post_none_peak_content(today, none_peak_alarm_volumn)
    print('\n天气预警信息发送：DONE')
    print('\n#####################################################################')
    print('\n请到D-CHAT查看信息！')