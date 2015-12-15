import urllib.request
import http.cookiejar
import re
import hashlib
import base64

class HiLink(object):
	"""华为HiLink自动切换数据连接开关状态"""
	re_csrf_token = re.compile(r'(?<="csrf_token" content=").+(?="/>)') # 预编译匹配csrf_token的正则表达式
	re_dataswitch = re.compile(r'(?<=<dataswitch>).+(?=</dataswitch>)') # 预编译匹配切换状态的正则表达式
	re_response = re.compile(r'(?<=<response>).+(?=</response>)') # 预编译匹配返回结果的正则表达式
	main_url = 'http://192.168.8.1/html/unicomhome.html' # 用于获取csrf_token的url
	dataswitch_url = 'http://192.168.8.1/api/dialup/mobile-dataswitch' # 数据开关api

	def __init__(self, user = 'admin', psw = 'hldh214'):
		'''
		user传入用户名
		psw传入密码
		'''
		super(HiLink, self).__init__()
		self.user = user
		self.psw = psw

	def login(self):
		'''
		构造xml模拟用户登录,记录cookies到opener里面
		'''
		login_url = 'http://192.168.8.1/api/user/login' # 登录api
		cookie = http.cookiejar.CookieJar() # 用cookiejar存储cookies
		opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))

		csrf_token = opener.open(self.main_url).read().decode()
		g_requestVerificationToken = self.re_csrf_token.findall(csrf_token)

		# 开始编码密码
		psw1 = hashlib.sha256(self.psw.encode()).hexdigest()
		psw2 = base64.b64encode(psw1.encode()).decode()
		psw3 = self.user + psw2 + g_requestVerificationToken[0]
		psw4 = hashlib.sha256(psw3.encode()).hexdigest().encode()
		psd = base64.b64encode(psw4).decode()
		# 编码结束

		login_data = '''<?xml version="1.0" encoding="UTF-8"?><request><Username>''' + self.user + '''</Username><Password>''' + psd + '''</Password><password_type>4</password_type></request>''' # 构造post数据

		opener.addheaders = [('__RequestVerificationToken', g_requestVerificationToken[0])] # 伪造csrf_token头

		login_res = opener.open(login_url, login_data.encode()).read().decode() # 登录
		login_res = self.re_response.findall(login_res)

		self.opener = opener
		#self.login_res = login_res

	def checkStatus(self):
		'''self.status == '0' 表示数据未开启
		   self.status == '1' 表示数据已开启
		'''
		self.status = self.opener.open(self.dataswitch_url).read().decode()
		self.status = self.re_dataswitch.findall(self.status)[0]

	def switchStatus(self):
		'''
		判断数据开启情况并做出相应动作
		'''
		switch_on_data = '''<?xml version="1.0" encoding="UTF-8"?><request><dataswitch>1</dataswitch></request>'''
		switch_off_data = '''<?xml version="1.0" encoding="UTF-8"?><request><dataswitch>0</dataswitch></request>'''
		if int(self.status):
			csrf_token = self.opener.open(self.main_url).read().decode()
			g_requestVerificationToken = self.re_csrf_token.findall(csrf_token)
			self.opener.addheaders = [('__RequestVerificationToken', g_requestVerificationToken[0])]
			data_switch_off = self.opener.open(self.dataswitch_url, switch_off_data.encode()).read().decode()
			response = self.re_response.findall(data_switch_off)[0]
			print(response)
		else:
			csrf_token = self.opener.open(self.main_url).read().decode()
			g_requestVerificationToken = self.re_csrf_token.findall(csrf_token)
			self.opener.addheaders = [('__RequestVerificationToken', g_requestVerificationToken[0])]
			data_switch_on = self.opener.open(self.dataswitch_url, switch_on_data.encode()).read().decode()
			response = self.re_response.findall(data_switch_on)[0]
			print(response)


if __name__ == '__main__':
	h = HiLink()
	h.login()
	h.checkStatus()
	h.switchStatus()
	input() #pause