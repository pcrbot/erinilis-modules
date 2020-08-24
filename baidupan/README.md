# 度盘直链解析

---

安装依赖
> pip install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple



文件夹丢到modules目录下
需要到bot的配置里的 MODULES_ON 添加 'baidupan'

例如hoshinov2如下配置和路径

文件丢到 hoshino/modules/baidupan

修改文件添加模块 `hoshino/config/__bot__.py`
```python
MODULES_ON = {
   'baidupan',
}
```

---
### 需要到度盘获取cookie值 `BDUSS`和`STOKEN`填入config.yml中

---

命令  | 说明 | 例
------------- | ------------- | -------------
p#或pan#  | 解析一个度盘链接 | p#分享地址 提取码<br>p#秒传链接
panhelp  | 显示链接下载帮助 | panhelp
