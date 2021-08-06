# 原神插件

---
之后杂项都更新到这个插件里 </br>

安装依赖
> pip install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple
>
> pip install sqlitedict -i https://pypi.tuna.tsinghua.edu.cn/simple


---

## 原神公告指令

命令  | 说明 | 例
------------- | ------------- | -------------
原神公告  | 相当于游戏内公告 |
原神公告#  | 查看某个公告详细信息 | 原神公告#1992
订阅原神公告 | 如果有新公告将推送到群内 |
取消订阅原神公告 | |
取消红点# | 取消游戏内的红点公告,只需要uid | 取消红点#105293904

## 设置材料收集提醒

命令  | 说明 | 例
------------- | ------------- | -------------
收集材料#材料名字  | 根据配置文件中材料的时间通知设定者 | 收集材料#水晶矿
收集材料#自定义10 | 自定义一个时间提醒 | 收集材料#探索16
收集材料# | 查看自己设定的材料列表 |

## 原神猜语音小游戏

命令  | 说明 | 例
------------- | ------------- | -------------
原神猜语音  | 开始原神猜语音 | 不指定语音则为中文
原神猜语音日 | 选择日语语音包 | 可选语音包 日 英 韩
原神猜语音排行榜 | 查看本群排行榜 | 原神猜语音排行榜
原神语音| 发送指定人物的随机语音 | 原神语音刻晴
更新原神语音资源 | 第一次安装时一定要选运行这个指令 |

<details>
<summary>示例</summary>

![image](./doc/guess_voice.jpeg)

![image](./doc/guess_voice_rank.jpeg)

</details>

## 原神抽卡

命令  | 说明 | 例
------------- | ------------- | -------------
原神十连  | 一次10连抽卡 |
原神一单  | 一次50连抽卡 |
原神切换卡池 | 可以切换为 限定\武器\常驻 | 原神切换卡池武器

<details>
<summary>示例</summary>

部分素材来自于 [Adachi-BOT](https://github.com/SilveryStar/Adachi-BOT)

![image](./doc/gacha.jpeg)

</details>

## 查询玩家信息

插件调用的是米游社角色信息的接口,查询的信息也是基于上面的基础信息<br>
需要到米游社获取cookie配置到`config.yml`文件里 `setting`下的`cookies`里

命令  | 说明 | 例
------------- | ------------- | -------------
ys#UID  | 查询一个UID信息 | ys#105293904
ys#@xxx | 查询群友的UID,必须能@到人 | ys#@xxx
ys#  | 查询用户上一次查询的UID信息 | ys#

<details>
<summary>示例</summary>

界面作者 [明见佬](https://github.com/A-kirami)

![image](./doc/player_info.jpeg)

</details>

## 深渊速查

[数据来源](https://spiral-abyss.appsample.com)

命令  | 说明 | 例
------------- | ------------- | -------------
原神深渊速查  | 查询一层深渊阵容推荐列表(不填参数默认12层) | 原神深渊速查11
原神深渊使用率 | 查询一层深渊角色使用率(不填参数默认12层) | 原神深渊使用率11

<details>
<summary>示例</summary>

![image](./doc/abyss_use_teams.jpeg)

![image](./doc/abyss_use_probability.jpeg)

</details>