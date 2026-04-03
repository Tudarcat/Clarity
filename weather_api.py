
import requests

def get_weather():
    # 使用和风天气API获取威海天气信息
    # 注意：这里使用的是免费API，需要注册获取自己的key
    # 这里使用一个示例key，可能会过期，实际使用时需要替换
    api_key = "3d6276e11436401c8a6f1773e0d9279b"
    location = "101120701"  # 威海的城市ID
    url = f"https://devapi.qweather.com/v7/weather/7d?location={location}&key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["code"] == "200":
            daily_forecast = data["daily"]
            
            print("威海未来7天天气预报：")
            for day in daily_forecast:
                date = day["fxDate"]
                text_day = day["textDay"]
                text_night = day["textNight"]
                temp_max = day["tempMax"]
                temp_min = day["tempMin"]
                wind_dir = day["windDirDay"]
                wind_scale = day["windScaleDay"]
                
                print(f"{date}：{text_day}转{text_night}，温度{temp_min}°C-{temp_max}°C，{wind_dir}{wind_scale}级")
        else:
            print(f"获取天气信息失败：{data['code']}")
    except Exception as e:
        print(f"请求出错：{e}")

get_weather()
