# 逐步执行，代码实现

# 写代码时碰到问题是正常的。它是一个“执行→遇到问题→解决问题→继续执行”的循环，不过相信循环总有break的时刻，问题是可以被解决的鸭！

## 版本1.0：封装函数，自定属性

# 一个函数只负责一个单一的功能，以便编写、理解和维护。
## 展示角色
def show_role(player_life,player_attack,enemy_life,enemy_attack):
    print('【玩家】\n血量：%s\n攻击：%s'%(player_life,player_attack))
    print('------------------------')
    print('【敌人】\n血量：%s\n攻击：%s'%(enemy_life,enemy_attack))
    print('-----------------------')

show_role(100,35,105,33)

# 双方PK
import time 
def pk_role(player_life,player_attack,enemy_life,enemy_attack):
    while player_life > 0 and enemy_life > 0:
        player_life = player_life - enemy_attack
        enemy_life = enemy_life - player_attack
        time.sleep(1)
        print('你发起了攻击，【敌人】剩余血量%s'%(enemy_life))
        print('敌人向你发起了攻击，【玩家】剩余血量%s'%(player_life))
        print('-----------------------')

# 打印战果
#打印战果，函数式代码
def show_result(player_life,enemy_life):
    if player_life > 0 and enemy_life <= 0:
        print('敌人死翘翘了，这局你赢了')
    elif player_life <= 0 and enemy_life > 0:
        print('悲催，这局敌人把你干掉了！')
    else:
        print('哎呀，这局你和敌人同归于尽了！')
    print('-----------------------')

# 版本1融合
import time

# 展示角色
def show_role(player_life,player_attack,enemy_life,enemy_attack):
    print('【玩家】\n血量：%s\n攻击：%s'%(player_life,player_attack))
    print('------------------------')
    time.sleep(1)
    print('【敌人】\n血量：%s\n攻击：%s'%(enemy_life,enemy_attack))
    print('-----------------------')

# 双方PK
def pk_role(player_life,player_attack,enemy_life,enemy_attack):
    while player_life > 0 and enemy_life > 0:
        player_life = player_life - enemy_attack
        enemy_life = enemy_life - player_attack
        time.sleep(1)
        print('你发起了攻击，【敌人】剩余血量'+str(enemy_life))
        print('敌人向你发起了攻击，【玩家】剩余血量'+str(player_life))
        print('-----------------------')
    #把打印战果函数放在PK函数内部
    show_result(player_life,enemy_life) 
    
# 打印战果
def show_result(player_life,enemy_life):
    if player_life > 0 and enemy_life <= 0:
        print('敌人死翘翘了，这局你赢了')
    elif player_life <= 0 and enemy_life > 0:
        print('悲催，这局敌人把你干掉了！')
    else:
        print('哎呀，这局你和敌人同归于尽了！')
    print('-----------------------')

# （主函数）展开战斗全流程
def main(player_life,player_attack,enemy_life,enemy_attack):
    show_role(player_life,player_attack,enemy_life,enemy_attack)
    pk_role(player_life,player_attack,enemy_life,enemy_attack)
    #删除了调用show_role函数的1行代码

main(100,35,105,33)

# 函数是减少代码冗余和增加代码复用的有效手段。

# 版本2.0：随机角色，随机属性
import random

player_list =  ['【狂血战士】','【森林箭手】','【光明骑士】','【独行剑客】','【格斗大师】','【枪弹专家】']

#随机选取三个角色
choice=random.sample(player_list,3)
print(choice)

import time,random

player_list =  ['【狂血战士】','【森林箭手】','【光明骑士】','【独行剑客】','【格斗大师】','【枪弹专家】']
enemy_list = ['【暗黑战士】','【黑暗弩手】','【暗夜骑士】','【嗜血刀客】','【首席刺客】','【陷阱之王】']
players = random.sample(player_list,3)  
enemies = random.sample(enemy_list,3)
player_info = {}
enemy_info = {}

# 随机生成两种属性
def born_role():
    life = random.randint(100,180)
    attack = random.randint(30,50)
    return life,attack  # return 多个元素时，返回一个元组（昨天课堂有讲）
    
# 给角色生成随机属性，并展示角色信息。
def show_role():
    for i in range(3):
        player_info[players[i]] = born_role()
        enemy_info[enemies[i]] = born_role()
    
    # 展示我方的3个角色
    print('----------------- 角色信息 -----------------')
    print('你的人物：')
    for i in range(3):
        print('%s  血量：%d  攻击：%d' 
        %(players[i],player_info[players[i]][0],player_info[players[i]][1]))
    print('--------------------------------------------')
    print('电脑敌人：')
    
    # 展示敌方的3个角色
    for i in range(3):
        print('%s  血量：%d  攻击：%d' 
        %(enemies[i],enemy_info[enemies[i]][0],enemy_info[enemies[i]][1]))
    print('--------------------------------------------')

show_role()



## 版本3.0：询问玩家出场顺序

# 由于要让玩家自由选择顺序，所以要用到input()函数。


players = ['【狂血战士】','【森林箭手】','【光明骑士】']

order_dict = {}
# 新建字典，存储顺序
for i in range(3):
    order = int(input('你想将 %s 放在第几个上场？(输入数字1~3)' % players[i]))
    order_dict[order] = players[i]

players = []
for i in range(1,4):
    players.append(order_dict[i]) 

print('\n我方角色的出场顺序是：%s、%s、%s' % (players[0],players[1],players[2]))


import random

# 将需要的数据和固定变量放在开头
player_list =  ['【狂血战士】','【森林箭手】','【光明骑士】','【独行剑客】','【格斗大师】','【枪弹专家】']
enemy_list = ['【暗黑战士】','【黑暗弩手】','【暗夜骑士】','【嗜血刀客】','【首席刺客】','【陷阱之王】']
players = random.sample(player_list,3)  
enemies = random.sample(enemy_list,3)
player_info = {}
enemy_info = {}

# 随机生成角色的属性
def born_role():
    life = random.randint(100,180)
    attack = random.randint(30,50)
    return life,attack

# 生成和展示角色信息
def show_role():
    for i in range(3):
        player_info[players[i]] = born_role()
        enemy_info[enemies[i]] = born_role()
    
    # 展示我方的3个角色
    print('----------------- 角色信息 -----------------')
    print('你的人物：')
    for i in range(3):
        print('%s  血量：%d  攻击：%d' 
        %(players[i],player_info[players[i]][0],player_info[players[i]][1]))
    print('--------------------------------------------')
    print('电脑敌人：')
    
    # 展示敌方的3个角色
    for i in range(3):
        print('%s  血量：%d  攻击：%d' 
        %(enemies[i],enemy_info[enemies[i]][0],enemy_info[enemies[i]][1]))
    print('--------------------------------------------')
    input('请按回车键继续。\n')  # 为了让玩家更有控制感，可以插入类似的代码来切分游戏进程。

# 角色排序，选择出场顺序。
def order_role(): 
    global players
    order_dict = {}
    for i in range(3):
        order = int(input('你想将 %s 放在第几个上场？(输入数字1~3)'%(players[i])))
        order_dict[order] = players[i]  

    players = []
    for i in range(1,4):
        players.append(order_dict[i]) 
    
    print('\n我方角色的出场顺序是：%s、%s、%s' %(players[0],players[1],players[2]))
    print('敌方角色的出场顺序是：%s、%s、%s' %(enemies[0],enemies[1],enemies[2]))

def main():
    show_role()
    order_role()

main()


# 版本4.0：3V3战斗，输出战果


import time

players = ['【狂血战士】','【森林箭手】','【光明骑士】']
enemies = ['【暗黑战士】','【黑暗弩手】','【暗夜骑士】']
player_info = {'【狂血战士】':(105,35),'【森林箭手】':(105,35),'【光明骑士】':(105,35)}
enemy_info = {'【暗黑战士】':(105,35),'【黑暗弩手】':(105,35),'【暗夜骑士】':(105,35)}
input('按回车开始简化版游戏：')

# 角色PK
def pk_role(): 
    round = 1  
    score = 0
    for i in range(3):  # 一共要打三局
        player_name = players[i] 
        enemy_name = enemies[i]  
        player_life = player_info[players[i]][0]
        player_attack = player_info[players[i]][1]
        enemy_life = enemy_info[enemies[i]][0]
        enemy_attack = enemy_info[enemies[i]][1]
        # 每一局开战前展示战斗信息
        print('\n----------------- 【第%d局】 -----------------' % round)
        print('玩家角色：%s vs 敌方角色：%s ' %(player_name,enemy_name))
        print('%s 血量：%d  攻击：%d' %(player_name,player_life,player_attack))
        print('%s 血量：%d  攻击：%d' %(enemy_name,enemy_life,enemy_attack))
        print('--------------------------------------------')
        input('请按回车键继续。\n')
        # 开始判断血量是否都大于零，然后互扣血量。
        while player_life > 0 and enemy_life > 0:
            enemy_life = enemy_life - player_attack
            player_life = player_life - enemy_attack
            print('%s发起了攻击，%s剩余血量%d'%(player_name,enemy_name,enemy_life))
            print('%s发起了攻击，%s剩余血量%d'%(enemy_name,player_name,player_life))
            print('--------------------------------------------')
            time.sleep(1)
        else:  # 每局的战果展示，以及分数score和局数的变化。
            print(show_result(player_life,enemy_life)[1])
            # 调用show_result()函数，打印返回元组中的第一个元素result。
            score += int(show_result(player_life,enemy_life)[0])
            # 调用show_result()函数，完成计分变动。
            round += 1
    input('\n点击回车，查看比赛的最终结果\n')
    if score > 0:
        print('【最终结果：你赢了！】\n')
    elif score < 0:
        print('【最终结果：你输了！】\n')
    else:
        print('【最终结果：平局！】\n')

# 返回单局战果和计分法所加分数。
def show_result(player_life,enemy_life):  # 注意：该函数要设定参数，才能判断单局战果。
    if player_life > 0 and enemy_life <= 0:
        result = '\n敌人死翘翘了，你赢了！'
        return 1,result  # 返回元组(1,'\n敌人死翘翘了，你赢了！')
    elif player_life <= 0 and enemy_life > 0:        
        result = '\n悲催，敌人把你干掉了！'
        return -1,result
    else :
        result = '\n哎呀，你和敌人同归于尽了！'
        return 0,result

pk_role()

# 最终代码
import time,random

# 需要的数据和变量放在开头
player_list =  ['【狂血战士】','【森林箭手】','【光明骑士】','【独行剑客】','【格斗大师】','【枪弹专家】']
enemy_list = ['【暗黑战士】','【黑暗弩手】','【暗夜骑士】','【嗜血刀客】','【首席刺客】','【陷阱之王】']
players = random.sample(player_list,3)  
enemies = random.sample(enemy_list,3)
player_info = {}
enemy_info = {}

# 随机生成角色的属性
def born_role():
    life = random.randint(100,180)
    attack = random.randint(30,50)
    return life,attack

# 生成和展示角色信息
def show_role():
    for i in range(3):
        player_info[players[i]] = born_role()
        enemy_info[enemies[i]] = born_role()
    
    # 展示我方的3个角色
    print('----------------- 角色信息 -----------------')
    print('你的人物：')
    for i in range(3):
        print('%s  血量：%d  攻击：%d' 
        %(players[i],player_info[players[i]][0],player_info[players[i]][1]))
    print('--------------------------------------------')
    print('电脑敌人：')
    
    # 展示敌方的3个角色
    for i in range(3):
        print('%s  血量：%d  攻击：%d' 
        %(enemies[i],enemy_info[enemies[i]][0],enemy_info[enemies[i]][1]))
    print('--------------------------------------------')
    input('请按回车键继续。\n')  # 为了让玩家更有控制感，可以插入类似的代码来切分游戏进程。

# 角色排序，选择出场顺序。
def order_role(): 
    global players
    order_dict = {}
    for i in range(3):
        order = int(input('你想将 %s 放在第几个上场？(输入数字1~3)'% players[i]))
        order_dict[order] = players[i]  

    players = []
    for i in range(1,4):
        players.append(order_dict[i]) 
    
    print('\n我方角色的出场顺序是：%s、%s、%s' %(players[0],players[1],players[2]))
    print('敌方角色的出场顺序是：%s、%s、%s' %(enemies[0],enemies[1],enemies[2]))

# 角色PK
def pk_role(): 
    round = 1  
    score = 0
    for i in range(3):  # 一共要打三局
        player_name = players[i]  
        enemy_name = enemies[i] 
        player_life = player_info[players[i]][0]
        player_attack = player_info[players[i]][1]
        enemy_life = enemy_info[enemies[i]][0]
        enemy_attack = enemy_info[enemies[i]][1]

        # 每一局开战前展示战斗信息
        print('\n----------------- 【第%d局】 -----------------' % round)
        print('玩家角色：%s vs 敌方角色：%s ' %(player_name,enemy_name))
        print('%s 血量：%d  攻击：%d' %(player_name,player_life,player_attack))
        print('%s 血量：%d  攻击：%d' %(enemy_name,enemy_life,enemy_attack))
        print('--------------------------------------------')
        input('请按回车键继续。\n')

        # 开始判断血量是否都大于零，然后互扣血量。
        while player_life > 0 and enemy_life > 0:
            enemy_life = enemy_life - player_attack
            player_life = player_life - enemy_attack
            print('%s发起了攻击，%s剩余血量%d' % (player_name,enemy_name,enemy_life))
            print('%s发起了攻击，%s剩余血量%d' % (enemy_name,player_name,player_life))
            print('--------------------------------------------')
            time.sleep(1)
        else:  # 每局的战果展示，以及分数score和局数的变化。
            # 调用show_result()函数，打印返回元组中的result。
            print(show_result(player_life,enemy_life)[1])
            # 调用show_result()函数，完成计分变动。
            score += int(show_result(player_life,enemy_life)[0])
            round += 1
    input('\n点击回车，查看比赛的最终结果\n')

    if score > 0:
        print('【最终结果：你赢了！】\n')
    elif score < 0:
        print('【最终结果：你输了！】\n')
    else:
        print('【最终结果：平局！】\n')

# 返回单局战果和计分法所加分数。
def show_result(player_life,enemy_life):  # 注意：该函数要设定参数，才能判断单局战果。
    if player_life > 0 and enemy_life <= 0:
        result = '\n敌人死翘翘了，你赢了！'
        return 1,result  # 返回元组(1,'\n敌人死翘翘了，你赢了！')，类似角色属性的传递。
    elif player_life <= 0 and enemy_life > 0:        
        result = '\n悲催，敌人把你干掉了！'
        return -1,result
    else :
        result = '\n哎呀，你和敌人同归于尽了！'
        return 0,result

# （主函数）展开战斗流程
def main():
    show_role()
    order_role()
    pk_role()

# 启动程序（即调用主函数）
main()