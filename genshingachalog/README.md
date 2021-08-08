# 原神卡池记录统计插件

---
(血统验证插件)<br>

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

你需要fork一份网页进行数据获取 https://github.com/yuyumoko/genshin-gacha-analyzer  <br>
fork后在 `/src/pages/LoadPage.tsx` 的第`28`行的`host`变量里修改你的bot地址(必须有公网)<br>
修改完毕后你可以直接部署到actions中, 然后在`config.yml`文件里的 `gacha_analyzer_webs`填写对应的网站即可<br>

---

可以直接在群文件上传`gacha-list-101717153.json`这个文件格式的抽卡历史记录 用于合并服务器卡池记录

命令  | 说明 | 例
------------- | ------------- | -------------
原神卡池绑定  | 绑定卡池用于查询 | 原神卡池绑定
原神卡池进度  | 查询限定,武器,常驻池已经抽了多少发 | 原神卡池进度
原神卡池统计  | 生成xlsx文件,使用卡池分析页面进行获取分析 | 原神卡池统计

# 统计示例

@？ 数据已更新, 请访问: <br>
https://genshin-gacha-analyzer.pages.dev/?uid=105293904 <br>
https://erinilis-gacha-analyzer.vercel.app/?uid=105293904 <br>
https://yuyumoko.github.io/genshin-gacha-analyzer/?uid=105293904 <br>

# 鸣谢(数据参考)

https://github.com/voderl/genshin-gacha-analyzer <br>
https://nga.178.com/read.php?tid=25004616 <br>
https://nga.178.com/read.php?tid=25011594
