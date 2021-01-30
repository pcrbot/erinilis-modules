# 原神卡池记录统计插件

---
(血统验证插件)<br>
*注意 此插件需要用户下载额外程序到PC上获取原神的authkey值.<br>
不会对游戏进行任何操作,仅仅是通过代理系统网络链接捕获原神卡池页面地址.<br>
如果怕造成风险, 谨慎安装


安装依赖
> pip install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple
>
> pip install sqlitedict -i https://pypi.tuna.tsinghua.edu.cn/simple


文件夹丢到modules目录下 需要到bot的配置里的 MODULES_ON 添加 'genshingachalog'

例如hoshinov2如下配置和路径

文件丢到 hoshino/modules/genshingachalog

修改文件添加模块 `hoshino/config/__bot__.py`

```python
MODULES_ON = {
    'genshingachalog',
}
```

---

命令  | 说明 | 例
------------- | ------------- | -------------
原神卡池进度  | 查询限定,武器,常驻池已经抽了多少发 | 原神卡池进度
原神卡池统计#限定/武器/常驻  | 统计全部5星出货概率,以及预测出货率 | 原神卡池统计#限定

# 鸣谢(数据参考)

https://nga.178.com/read.php?tid=25004616 <br>
https://nga.178.com/read.php?tid=25011594
