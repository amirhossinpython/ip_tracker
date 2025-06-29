import sys
import subprocess
import requests
import socket
import time
import json
import os
import webbrowser
from datetime import datetime
import matplotlib.pyplot as plt
class IPTrackerPro:
    def __init__(self):
        self._install_requirements()
        self.base_url = "http://ip-api.com/php/"
        self.history_file = "ip_history.json"
        self.history = self._load_history()
        self.rate_limit = {
            'remaining': 45,
            'reset_time': 0,
            'last_request': 0
        }
        
    def _install_requirements(self):
        """نصب خودکار کتابخانه‌های مورد نیاز"""
        required_libs = {
            'requests': 'requests',
            'phpserialize': 'phpserialize',
            'folium': 'folium',
            'matplotlib': 'matplotlib',
            'IPython': 'ipython'
        }
        
        for lib, pkg in required_libs.items():
            try:
                __import__(lib)
            except ImportError:
                print(f"📦 در حال نصب کتابخانه {lib}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
    
    def _load_history(self):
        """بارگذاری تاریخچه جستجوها"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_history(self, ip_data):
        """ذخیره اطلاعات جستجو در تاریخچه"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'ip': ip_data.get('query'),
            'country': ip_data.get('country'),
            'city': ip_data.get('city'),
            'isp': ip_data.get('isp'),
            'lat': ip_data.get('lat'),
            'lon': ip_data.get('lon')
        }
        self.history.append(entry)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def _check_rate_limit(self):
        """بررسی محدودیت درخواست به API"""
        now = time.time()
        if self.rate_limit['remaining'] <= 0 and now < self.rate_limit['reset_time']:
            wait_time = self.rate_limit['reset_time'] - now
            raise Exception(f"⏳ محدودیت درخواست! لطفاً {wait_time:.1f} ثانیه صبر کنید.")
    
    def _update_rate_limit(self, headers):
        """به‌روزرسانی اطلاعات محدودیت درخواست"""
        self.rate_limit['remaining'] = int(headers.get('X-Rl', 45))
        self.rate_limit['reset_time'] = time.time() + int(headers.get('X-Ttl', 60))
        self.rate_limit['last_request'] = time.time()
    
    def get_public_ip(self):
        """دریافت IP عمومی کاربر"""
        try:
            return requests.get('https://api.ipify.org').text
        except Exception as e:
            raise Exception(f"❌ خطا در دریافت IP عمومی: {str(e)}")
    
    def validate_ip(self, ip_address):
        """اعتبارسنجی آدرس IP"""
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False
    
    def get_ip_info(self, ip_address=None, lang='en', fields=3207167):
        """
        دریافت اطلاعات کامل IP از API
        :param ip_address: آدرس IP (اگر None باشد IP عمومی کاربر استفاده می‌شود)
        :param lang: زبان خروجی (en, de, es, fr, etc.)
        :param fields: فیلدهای درخواستی (کد عددی)
        :return: دیکشنری اطلاعات IP
        """
        self._check_rate_limit()
        
        if not ip_address:
            ip_address = self.get_public_ip()
        elif not self.validate_ip(ip_address):
            raise ValueError("آدرس IP نامعتبر است")
        
        url = f"{self.base_url}{ip_address}?fields={fields}&lang={lang}"
        
        try:
            response = requests.get(url)
            self._update_rate_limit(response.headers)
            
            if response.status_code == 429:
                raise Exception("محدودیت درخواست! لطفاً بعداً تلاش کنید.")
            
            if response.status_code != 200:
                raise Exception(f"خطای API با کد وضعیت {response.status_code}")
            
            # تبدیل داده PHP-serialized به دیکشنری
            from phpserialize import loads
            data = loads(response.content)
            
            # تبدیل bytes به string
            decoded_data = {}
            for k, v in data.items():
                if isinstance(k, bytes):
                    k = k.decode('utf-8')
                if isinstance(v, bytes):
                    v = v.decode('utf-8')
                decoded_data[k] = v
            
            self._save_history(decoded_data)
            return decoded_data
            
        except Exception as e:
            raise Exception(f"خطا در دریافت اطلاعات: {str(e)}")
    
    def display_location_info(self, ip_info):
        """نمایش اطلاعات مکانی IP"""
        if not ip_info or 'status' not in ip_info or ip_info['status'] != 'success':
            print("❌ اطلاعات مکانی نامعتبر است")
            return
        
        print("\n📍 اطلاعات مکانی")
        print("-------------------")
        print(f"🌍 کشور: {ip_info.get('country', 'N/A')} ({ip_info.get('countryCode', 'N/A')})")
        print(f"🏙 منطقه: {ip_info.get('regionName', 'N/A')} ({ip_info.get('region', 'N/A')})")
        print(f"🏡 شهر: {ip_info.get('city', 'N/A')}")
        print(f"📮 کد پستی: {ip_info.get('zip', 'N/A')}")
        print(f"📍 مختصات: {ip_info.get('lat', 'N/A')}, {ip_info.get('lon', 'N/A')}")
        print(f"⏰ منطقه زمانی: {ip_info.get('timezone', 'N/A')}")
    
    def display_network_info(self, ip_info):
        """نمایش اطلاعات شبکه"""
        if not ip_info or 'status' not in ip_info or ip_info['status'] != 'success':
            print("❌ اطلاعات شبکه نامعتبر است")
            return
        
        print("\n🖥️ اطلاعات شبکه")
        print("-------------------")
        print(f"🔌 ISP: {ip_info.get('isp', 'N/A')}")
        print(f"🏢 سازمان: {ip_info.get('org', 'N/A')}")
        print(f"🖥 سیستم مستقل: {ip_info.get('as', 'N/A')}")
        print(f"🆔 آدرس IP: {ip_info.get('query', 'N/A')}")
    
    def generate_map_links(self, ip_info):
        """تولید لینک‌های مستقیم به نقشه‌های مختلف"""
        if 'lat' not in ip_info or 'lon' not in ip_info:
            return None
            
        lat = ip_info['lat']
        lon = ip_info['lon']
        city = ip_info.get('city', 'Unknown')
        country = ip_info.get('country', 'Unknown')
        
        return {
            'google_maps': f"https://www.google.com/maps?q={lat},{lon}",
            'openstreetmap': f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}",
            'bing_maps': f"https://www.bing.com/maps?cp={lat}~{lon}",
            'map_embed': f"https://maps.google.com/maps?output=embed&q={lat},{lon}",
            'yandex_maps': f"https://yandex.com/maps/?pt={lon},{lat}&z=12"
        }

    def display_map_links(self, ip_info):
        """نمایش لینک‌های نقشه در کنسول"""
        map_links = self.generate_map_links(ip_info)
        if not map_links:
            print("❌ اطلاعات موقعیت برای تولید لینک نقشه موجود نیست")
            return
            
        print("\n🗺️ لینک‌های نقشه:")
        print("-------------------")
        print(f"🌐 گوگل مپ: {map_links['google_maps']}")
        print(f"🗺️ OpenStreetMap: {map_links['openstreetmap']}")
        print(f"🔍 بینگ مپ: {map_links['bing_maps']}")
        print(f"🧭 Yandex Maps: {map_links['yandex_maps']}")
        print("\nبرای باز کردن خودکار نقشه در مرورگر، عدد مربوطه را وارد کنید:")
        print("1. گوگل مپ")
        print("2. OpenStreetMap")
        print("3. بینگ مپ")
        print("4. Yandex Maps")
        print("0. بازگشت")
        
        choice = input("انتخاب شما: ")
        if choice == '1':
            webbrowser.open(map_links['google_maps'])
        elif choice == '2':
            webbrowser.open(map_links['openstreetmap'])
        elif choice == '3':
            webbrowser.open(map_links['bing_maps'])
        elif choice == '4':
            webbrowser.open(map_links['yandex_maps'])
    
    def show_on_map(self, ip_info):
        """نمایش موقعیت روی نقشه"""
        try:
            from folium import Map, Marker
            from IPython.display import display
            
            if 'lat' not in ip_info or 'lon' not in ip_info:
                print("❌ اطلاعات موقعیت برای نمایش نقشه موجود نیست")
                return
            
            lat = float(ip_info['lat'])
            lon = float(ip_info['lon'])
            
            m = Map(location=[lat, lon], zoom_start=10)
            Marker(
                [lat, lon],
                popup=f"{ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}",
                tooltip=ip_info.get('query')
            ).add_to(m)
            
            display(m)
        except Exception as e:
            print(f"❌ خطا در نمایش نقشه: {str(e)}")
    
    def generate_report(self, ip_info):
        """تولید گزارش کامل"""
        if not ip_info:
            print("❌ اطلاعاتی برای تولید گزارش موجود نیست")
            return
        
        print("\n📊 گزارش کامل اطلاعات IP")
        print("=" * 50)
        self.display_location_info(ip_info)
        self.display_network_info(ip_info)
        print("\n🌐 نمایش موقعیت روی نقشه:")
        self.show_on_map(ip_info)
        self.display_map_links(ip_info)
        print("=" * 50)
    
    def history_analysis(self):
        """تجزیه و تحلیل تاریخچه جستجوها"""
        if not self.history:
            print("📭 تاریخچه جستجو خالی است")
            return
        
        try:
            
            
            # تحلیل کشورها
            countries = {}
            for entry in self.history:
                country = entry.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
            
            # نمودار کشورها
            plt.figure(figsize=(10, 6))
            plt.bar(countries.keys(), countries.values())
            plt.title('توزیع جستجوها بر اساس کشور')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            
            # تحلیل موقعیت‌های جغرافیایی
            if len(self.history) > 1:
                plt.figure(figsize=(10, 6))
                lats = [float(entry.get('lat', 0)) for entry in self.history if entry.get('lat')]
                lons = [float(entry.get('lon', 0)) for entry in self.history if entry.get('lon')]
                if lats and lons:
                    plt.scatter(lons, lats, alpha=0.5)
                    plt.title('نقشه پراکندگی موقعیت‌های جستجو شده')
                    plt.xlabel('طول جغرافیایی')
                    plt.ylabel('عرض جغرافیایی')
                    plt.grid(True)
                    plt.show()
            
            # نمایش آخرین جستجوها
            print("\n🔍 آخرین جستجوها:")
            for entry in self.history[-5:]:
                print(f"- {entry['timestamp']}: {entry['ip']} ({entry['city']}, {entry['country']})")
                
        except Exception as e:
            print(f"❌ خطا در تحلیل تاریخچه: {str(e)}")

    def export_history(self, format='json'):
        """صدور تاریخچه به فرمت‌های مختلف"""
        if not self.history:
            print("📭 تاریخچه جستجو خالی است")
            return
        
        filename = f"ip_history_export.{format}"
        try:
            if format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, indent=2, ensure_ascii=False)
            elif format == 'csv':
                import csv
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self.history[0].keys())
                    writer.writeheader()
                    writer.writerows(self.history)
            else:
                raise ValueError("فرمت پشتیبانی نشده")
            
            print(f"✅ تاریخچه با موفقیت در فایل {filename} ذخیره شد")
        except Exception as e:
            print(f"❌ خطا در صدور تاریخچه: {str(e)}")


if __name__ == "__main__":
    print("🛠️ در حال راه‌اندازی پروژه ردیابی IP...")
    tracker = IPTrackerPro()
    
    try:
       
        print("\n🔎 دریافت اطلاعات IP عمومی شما...")
        my_ip_info = tracker.get_ip_info()
        tracker.generate_report(my_ip_info)
        
        
        print("\n🔎 دریافت اطلاعات یک IP نمونه...")
        sample_ip = input("enter the ip >>=")   
        sample_info = tracker.get_ip_info(sample_ip, lang='en')
        tracker.generate_report(sample_info)
        
        # تحلیل تاریخچه
        print("\n📈 تحلیل تاریخچه جستجوها...")
        tracker.history_analysis()
        
        # صدور تاریخچه
        print("\n💾 صدور تاریخچه جستجوها...")
        tracker.export_history(format='json')
        tracker.export_history(format='csv')
        
    except Exception as e:
        print(f"❌ خطا: {str(e)}")
    finally:
        print("\n✅ پروژه با موفقیت اجرا شد!")
