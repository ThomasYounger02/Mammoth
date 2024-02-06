


# 在编程世界中，我们不需要什么知识都一把抓，而是遇到问题之后，产生了某种需求，才会去找对应的解决方案。

# 搜索关键词“发送邮件 python”

# 1.Python可以解决这个问题；2.方法是smtplib，email这两个模块。负责发送邮件的smtplib模块，和负责构造邮件内容的email模块。

# <aside>
# 💡 到底学习什么模块，关键在于你的需求，这样我们才能从需求出发找到对应的解决方案，解决自己的问题。

# </aside>

# - 浏览器里搜索关键词“smtplib python”。谷歌翻译。

# 需要向smtplib模块输入什么；smtplib模块能做什么；smtplib模块返回的是什么；常见的报错；SMTP对象有哪些方法及如何使用；一个应用实例。

# - 关键词换成 “smtplib 教程”。

# 中国人编写的内容。在可读性上，是要比官方文档好一些的，但缺点在于良莠不齐。你可以自行挑选适合自己的去阅读。

# 带着问题学习模块：

import smtplib

server = smtplib.SMTP()
server.connect(host, port)
server.login(username, password) 
server.sendmail(from_addr, to_addr, msg.as_string()) 
server.quit()

# SMTP (Simple Mail Transfer Protocol)翻译过来是“简单邮件传输协议”的意思，SMTP 协议是由源服务器到目的地服务器传送邮件的一组规则。可以简单理解为：我们需要通过SMTP指定一个服务器，这样才能把邮件送到另一个服务器。

# host是指定连接的邮箱服务器，你可以指定服务器的域名。通过搜索“xx邮箱服务器地址”，就可以找到。

# port 是“端口”的意思。端口属于计算机网络知识里的内容。需要指定SMTP服务使用的端口号，一般情况下SMTP默认端口号为25。

# QQ邮箱：

# smtplib 用于邮件的发信动作
import smtplib

# 发信方的信息：发信邮箱，QQ邮箱授权码
from_addr = 'xxx@qq.com'
password = '你的授权码数字'

# 收信方邮箱
to_addr = 'xxx@qq.com'

# 发信服务器
smtp_server = 'smtp.qq.com'

# 开启发信服务，这里使用的是加密传输
server = smtplib.SMTP_SSL()
server.connect(smtp_server,465)
# 登录发信邮箱
server.login(from_addr, password)
# 发送邮件
server.sendmail(from_addr, to_addr, msg.as_string())
# 关闭服务器
server.quit()


# “模块”和“包”的区别了，模块（module）一般是一个文件，而包（package）是一个目录，一个包中可以包含很多个模块，可以说包是“模块打包”组成的。

MIMEText(msg,type,chartset)
# msg：文本内容，可自定义
# type：文本类型，默认为plain（纯文本）
# chartset：文本编码，中文为“utf-8”
from email.mime.text import MIMEText

msg = MIMEText('send by python','plain','utf-8')

# 在看别人代码的时候，也可以寻找结构清晰的代码作为参考，这样我们找到有用知识的概率也会提高。
# smtplib 用于邮件的发信动作
import smtplib
from email.mime.text import MIMEText
# email 用于构建邮件内容

# 发信方的信息：发信邮箱，QQ 邮箱授权码
from_addr = 'xxx@qq.com'
password = '你的授权码数字'

# 收信方邮箱
to_addr = 'xxx@qq.com'

# 发信服务器
smtp_server = 'smtp.qq.com'

# 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
msg = MIMEText('send by python','plain','utf-8')

# 开启发信服务，这里使用的是加密传输
server = smtplib.SMTP_SSL()
server.connect(smtp_server,465)
# 登录发信邮箱
server.login(from_addr, password)
# 发送邮件
server.sendmail(from_addr, to_addr, msg.as_string())
# 关闭服务器
server.quit()