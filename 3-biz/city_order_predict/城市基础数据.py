#提取基础的数据
import pandas as pd
import numpy as np
import prestodb
import datetime as dt

#############################################################################################################
#数据库
#############################################################################################################
#Presto函数
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
    df_data = pd.DataFrame(rows)
    return df_data

#############################################################################################################
#历史数据
#############################################################################################################
#df_base数据
def build_history_data(s_date, e_date):
    sql = '''
        select
            t0.date_id as date_id
            ,t0.hour_id as hour_id
            ,t0.city_id as city_id
            ,calls
            ,coalesce(intensity, 0)
            ,coalesce(temperature, 0)
            ,coalesce(humidity, 0)
            ,coalesce(cloudrate, 0)
            ,coalesce(pm25, 0)
            ,coalesce(holiday_type, 0)
            ,coalesce(holiday_rank, 0)
            ,coalesce(special_holiday, 0)
            ,coalesce(exam, 0)
            ,coalesce(b_activities, 0)
            from
        (--呼叫
        select
            date_id
            ,hour_id
            ,city_id
            ,sum(case when is_td_call = 1 and source_type <> 2 then 1 else 0 end ) as calls       -- 呼叫数
        from
            (
            select 
                concat_ws('-', year, month, day) as date_id     
                ,city_id
                ,is_td_call
                ,is_td_grab
                ,driver_id
                ,source_type
                ,hour(a_birth_time) as hour_id
            from 
                gulfstream_dwd.dwd_order_call_grab_d
            where 
                1=1 
                and concat_ws('-', year, month, day) between '{s_date}' and '{e_date}'
                and product_category in (3,7,99,20,314)
                and city_id in (44,290,291,292,293,294,173,295,296,297,298,299,310,311,136,279,137,138,117,118,119,50,53,17,19,280,281,282,283,284,285,286,287,288,300,289,301,302,303,304,305,306,307,82,308,309)
            ) a 
        group by
            date_id
            ,hour_id
            ,city_id
        ) t0
    
        left join
        (--天气
        select 
            date_id
            ,hour_id
            ,city_id
            ,if(intensity_mmh < 0, 0, intensity_mmh) as intensity
            ,temperature
            ,humidity
            ,cloudrate
            ,pm25
        from
            (
            select 
                date_id 
                ,hour_id
                ,city_id
                ,avg(power(power(10, dbz / 10) / 200, 5 / 8) - 0.2051) as intensity_mmh
                ,avg(temperature) as temperature
                ,avg(humidity) as humidity
                ,avg(cloudrate) as cloudrate
                ,avg(pm25) as pm25
            from
                (
                select 
                    concat_ws('-', year, month, day) as date_id
                    ,substr(server_time1, 10,2) as hour_id
                    ,didi_cityid as city_id
                    ,case 
                        when (intensity + 0.15) * 16 * 5 > 70 then 70
                        else (intensity + 0.15) * 16 * 5
                        end as dbz
                    ,temperature
                    ,pm25
                    ,cloudrate
                    ,humidity
                from 
                    dm.caiyun
                where 
                    1=1
                    and concat_ws('-',year, month, day) between '{s_date}' and '{e_date}'
                    and intensity < 1
                    and city_name in ('阿坝藏族羌族自治州','安顺市','巴中市','保山市','毕节市','成都市','楚雄彝族自治州','达州市','大理白族自治州','德宏傣族景颇族自治州','德阳市','迪庆藏族自治州','甘孜藏族自治州','广安市','广元市','贵阳市','红河哈尼族彝族自治州','昆明市','乐山市','丽江市','凉山彝族自治州','临沧市','六盘水市','泸州市','眉山市','绵阳市','南充市','内江市','怒江傈僳族自治州','攀枝花市','普洱市','黔东南苗族侗族自治州','黔南布依族苗族自治州','黔西南布依族苗族自治州','曲靖市','遂宁市','铜仁市','文山壮族苗族自治州','西双版纳傣族自治州','雅安市','宜宾市','玉溪市','昭通市','重庆市','资阳市','自贡市','遵义市')
                )a0
            group by 
                date_id 
                ,hour_id
                ,city_id
            )a
        ) t1
        on t0.date_id = t1.date_id
            and t0.hour_id = t1.hour_id
            and t0.city_id = t1.city_id
    
        left join
        (--节日
        select
            concat_ws('-',year, month, day) as date_id
            ,holiday_type
            ,holiday_rank
        from
            cyyg_bi.holiday_tag_table
        where
            dt = '2019-01-01'
        ) t2
        on t0.date_id = t2.date_id
    
        left join
        (--特殊节日
        select
            concat_ws('-',year, month, day) as date_id
            ,city_id
            ,special_holiday
            ,exam
            ,b_activities
        from
            cyyg_bi.city_special_holiday_tag_table
        where
            dt = '2019-01-01'
        ) t3
        on t0.date_id = t3.date_id
            and t0.city_id = t3.city_id
        '''
    sql_format = sql.format(s_date = s_date, e_date= e_date)
    df_base_data = Presto(sql_format)
    #设置列名
    df_base_data.columns=['date_id','hour_id','city_id',
                          'calls','intensity','temperature','humidity','cloudrate','pm25',
                          'holiday_type','holiday_rank',
                          'special_holiday','exam','b_activities']
    #构建时间列
    df_base_data["time"] =  pd.to_datetime(df_base_data['date_id']) + pd.to_timedelta(df_base_data['hour_id'], unit='h')
    #删除多余的数据列
    df_base_data.drop(columns=['date_id','hour_id'], inplace=True)
    #数据格式转换
    df_base_data['calls']= df_base_data['calls'].astype('float')
    df_base_data['holiday_type']=df_base_data['holiday_type'].astype('int')
    df_base_data['holiday_rank']=df_base_data['holiday_rank'].astype('int')
    df_base_data['special_holiday']=df_base_data['special_holiday'].astype('int')
    df_base_data['exam']=df_base_data['exam'].astype('int')
    df_base_data['b_activities']=df_base_data['b_activities'].astype('int')
    #调整顺序
    column_list = ['time','city_id','calls',
                   'intensity','temperature','humidity','cloudrate','pm25',
                   'holiday_type','holiday_rank','special_holiday','exam','b_activities']
    df_base_data = df_base_data[column_list]
    return df_base_data

#############################################################################################################
#未来数据
#############################################################################################################
#df_future数据框架
def build_future_calls(last_date, num_day_pred):
    df_future_data=pd.DataFrame()
    #单个城市的future构建
    city_list=[44,290,291,292,293,294,173,295,296,297,298,299,310,311,136,279,137,138,117,118,119,50,53,17,19,280,281,282,283,284,285,286,287,288,300,289,301,302,303,304,305,306,307,82,308,309]
    for city_id in city_list:
        #构建future数据集
        pred_points = int(num_day_pred * 24)
        pred_date = pd.date_range(start=last_date, periods=pred_points + 1, freq="1h")
        pred_date = pred_date[pred_date > last_date]
        future_data = pd.DataFrame({"time": pred_date, "calls": np.zeros(len(pred_date))})
        future_data['city_id'] = city_id
        df_future_data = df_future_data.append(future_data)
    return df_future_data

#df_future天气预测数据获取
def get_future_weather():
    now_time = dt.date.today().strftime('%Y-%m-%d')
    sql = '''
        select
            city_id
            ,hour_precipitation_48 as intensity
            ,hour_temperature_48 as temperature
            ,hour_humidity_48 as humidity
            ,hour_cloudrate_48 as cloudrate
            ,hour_pm25_48 as pm25
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
                 ,hour_humidity_48
                 ,hour_cloudrate_48
                 ,row_number() OVER (PARTITION BY city_name ORDER BY server_time1 DESC) as rn
            from
                pbs_dw.dwv_weather_h
            where
                1=1
                and concat_ws('-',year,month,day,hour) = concat_ws('-','{now_time}','00')
                and city_name in ('成都市','绵阳市','自贡市','宜宾市','普洱市','凉山彝族自治州','怒江傈僳族自治州','德阳市','文山壮族苗族自治州','昆明市','泸州市','西双版纳傣族自治州','广元市','铜仁市','大理白族自治州','玉溪市','安顺市','遂宁市','广安市','眉山市','黔南布依族苗族自治州','内江市','临沧市','资阳市','红河哈尼族彝族自治州','迪庆藏族自治州','达州市','黔东南苗族侗族自治州','德宏傣族景颇族自治州','贵阳市','楚雄彝族自治州','保山市','巴中市','南充市','毕节市','黔西南布依族苗族自治州','乐山市','攀枝花市','昭通市','丽江市','六盘水市','曲靖市','遵义市','雅安市')
            )a 
        where
            rn =1
    '''
    sql_format = sql.format(now_time = now_time)
    df_future_data = Presto(sql_format)
    df_future_data.columns=['city_id','intensity','temperature','humidity','cloudrate','pm25']
    return df_future_data


#df_future天气预测数据
def buil_future_weather(data):
    #取出所有的城市
    city_list = list(data.city_id.value_counts().index)
    weather = []
    #循环提取每个城市的数据
    for city_id in city_list:
        df_city = data[data['city_id']==city_id]
        #取出天气数据
        df_intensity = df_city['intensity' ][df_city['intensity' ].index[0]]
        df_temperature = df_city['temperature' ][df_city['temperature' ].index[0]]
        df_humidity = df_city['humidity' ][df_city['humidity' ].index[0]]
        df_cloudrate = df_city['cloudrate' ][df_city['cloudrate' ].index[0]]
        df_pm25 = df_city['pm25' ][df_city['pm25' ].index[0]]
        #key相同
        key_list = list(df_temperature.keys())
        #数据展开
        for key in key_list:
            weather.append({'date_id' :key[0:10],
                           'hour_id' :int(key[11:13]),
                           'city_id': city_id,
                           'intensity' :df_intensity[key],
                           'temperature' :df_temperature[key],
                           'humidity' :df_humidity[key],
                           'cloudrate' :df_cloudrate[key],
                           'pm25' :df_pm25[key]
                          })
    weather = pd.DataFrame(weather, columns=['date_id','hour_id','city_id','intensity','temperature','humidity','cloudrate','pm25'])
    #构建时间列
    weather["time"] =  pd.to_datetime(weather['date_id']) + pd.to_timedelta(weather['hour_id'], unit='h')
    #删除多余的数据列
    weather.drop(columns=['date_id','hour_id'], inplace=True)
    #重置索引
    weather.reset_index(inplace=True,drop=True)
    return weather
#############################################################################################################
#df_future节日部分
def build_future_holiday(s_date, num_day_pred):
    sql = '''
        select
            t0.date_id as date_id
            ,t1.city_id as city_id
            ,t0.holiday_type as holiday_type
            ,t0.holiday_rank as holiday_rank
            ,t1.special_holiday as special_holiday
            ,t1.exam as exam
            ,t1.b_activities as b_activities
        from
            (--节日
            select
                concat_ws('-',year, month, day) as date_id
                ,holiday_type
                ,holiday_rank
            from
                cyyg_bi.holiday_tag_table
            where
                dt = '2019-01-01'
            ) t0
        
            left join
            (--特殊节日
            select
                concat_ws('-',year, month, day) as date_id
                ,city_id
                ,special_holiday
                ,exam
                ,b_activities
            from
                cyyg_bi.city_special_holiday_tag_table
            where
                dt = '2019-01-01'
            ) t1
            on t0.date_id = t1.date_id
        where
            1=1
            and t0.date_id between '{s_date}' and  date_add('{s_date}',{num_day_pred})
    '''
    sql_format = sql.format(s_date = s_date, num_day_pred= num_day_pred)
    df_future_data = Presto(sql_format)
    df_future_data.columns=['date_id','city_id','holiday_type','holiday_rank','special_holiday','exam','b_activities']
    #将city_id转换为整数
    df_future_data['city_id'] = df_future_data['city_id'].astype('int')
    return df_future_data

#############################################################################################################
#df_future数据
def build_future_data(last_date, num_day_pred):
    #框架部分
    df_future_data = build_future_calls(last_date, num_day_pred)
    #天气部分
    future_weature = get_future_weather()
    df_future_data_weather = buil_future_weather(future_weature)
    #节日部分
    s_date = (last_date + dt.timedelta(days=1)).strftime('%Y-%m-%d')
    df_future_data_holiday = build_future_holiday(s_date, num_day_pred)
    #重新构建日期和小时
    df_future_data_holiday_ext=pd.DataFrame()
    for i in range(24):
        df_sub = df_future_data_holiday.copy()
        df_sub['hour_id'] = i
        df_future_data_holiday_ext = df_future_data_holiday_ext.append(df_sub)
    #构建时间列
    df_future_data_holiday_ext["time"] =  pd.to_datetime(df_future_data_holiday_ext['date_id']) + pd.to_timedelta(df_future_data_holiday_ext['hour_id'], unit='h')
    #删除多余的数据列
    df_future_data_holiday_ext.drop(columns=['date_id','hour_id'], inplace=True)
    #数据合并
    df_future_data = pd.merge(df_future_data, df_future_data_weather, how='left', on=['time', 'city_id'])
    df_future_data = pd.merge(df_future_data, df_future_data_holiday_ext, how='left', on=['time', 'city_id'])
    #填充空值
    df_future_data.fillna(0,inplace=True)
    #数据格式转换
    df_future_data['intensity']= df_future_data['intensity'].astype('float')
    df_future_data['temperature']= df_future_data['temperature'].astype('float')
    df_future_data['humidity']= df_future_data['humidity'].astype('float')
    df_future_data['cloudrate']= df_future_data['cloudrate'].astype('float')
    df_future_data['pm25']= df_future_data['pm25'].astype('float')
    df_future_data['holiday_type']=df_future_data['holiday_type'].astype('int')
    df_future_data['holiday_rank']=df_future_data['holiday_rank'].astype('int')
    df_future_data['special_holiday']=df_future_data['special_holiday'].astype('int')
    df_future_data['exam']=df_future_data['exam'].astype('int')
    df_future_data['b_activities']=df_future_data['b_activities'].astype('int')
    #调整顺序
    column_list = ['time','city_id','calls',
                   'intensity','temperature','humidity','cloudrate','pm25',
                   'holiday_type','holiday_rank','special_holiday','exam','b_activities']
    df_future_data = df_future_data[column_list]
    return df_future_data