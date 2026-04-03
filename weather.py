
import requests
from bs4 import BeautifulSoup

def get_weather_info():
    url = "http://www.weather.com.cn/weather/101120701.shtml"
    try:
        response = requests.get(url)
        response.encoding = "utf-8"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            weather_list = []
            
            # 找到天气预报的容器
            weather_container = soup.find("div", {"id": "7d"})
            if weather_container:
                # 找到所有的日期、天气、温度和风力信息
                date_elements = weather_container.find_all("h1")
                weather_elements = weather_container.find_all("p", {"class": "wea"})
                temp_elements = weather_container.find_all("p", {"class": "tem"})
                wind_elements = weather_container.find_all("p", {"class": "win"})
                
                # 提取信息
                for i in range(len(date_elements)):
                    date = date_elements[i].text.strip()
                    weather = weather_elements[i].text.strip()
                    temp = temp_elements[i].text.strip()
                    wind = wind_elements[i].text.strip()
                    
                    weather_list.append({
                        "date": date,
                        "weather": weather,
                        "temperature": temp,
                        "wind": wind
                    })
            
            return weather_list
        else:
            print("请求失败，状态码：", response.status_code)
            return None
    except Exception as e:
        print("请求出错：", e)
        return None

# 调用函数获取天气信息
weather_info = get_weather_info()

# 打印天气信息
if weather_info:
    print("威海最近天气情况：")
    for item in weather_info:
        print(f"{item['date']}：{item['weather']}，{item['temperature']}，{item['wind']}")
else:
    print("无法获取天气信息")
