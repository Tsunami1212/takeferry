# TakeFerry 中文使用指南

[英文项目介绍与编剧工作流](README.md) · [Hermes 配置指南](docs/setup.md) · [验证记录](docs/verification.md)

## 先试一个镜头

示例里，编剧要拍一条五秒的竖屏镜头。A 图定女主的脸，B 图只管灯光。她在第 2 秒听见钥匙声时回头，雨声一直留着。先在 LibTV 试固定机位，再把同一镜头交给小云雀对拍。两张画布都是模拟的，视频是随包提供的分镜，运行全程离线，消耗 0 平台积分。

从源码目录运行，需要 Python 3.9 或更高版本。

```sh
python3 -m takeferry demo --output rainy-door-demo
```

也可以从[发行页](https://github.com/Tsunami1212/takeferry/releases/tag/v0.1.0-alpha.1)下载 `takeferry.pyz`，运行 `python3 takeferry.pyz demo --output rainy-door-demo`。

打开输出目录里的 `rain-at-the-door.zip`。原片有五秒，剪辑单上记着编剧选中的一段，从第 1 秒到第 4.5 秒。同一目录里，`canvases.json` 可以查看参考图连到了哪个节点，`takes.json` 记录了四条试拍各自从哪一版改来，`branch-camera-movement/SKILL.md` 是这次拍法生成的 Hermes 私有技能草稿。

## 使用自己的平台账号

把一场戏贴进自己的 Hermes，确认分镜后挑一镜，再指定先去哪家。Agent 通过 MCP 在对应平台的原画布上建节点、接参考图、写提示词和选模型。真实生成需要你批准，使用所选平台账号的积分。首个公开版本的双平台付费实拍和私有技能在真实 Hermes 中的保存仍待验证。[接入步骤](docs/setup.md) · [验证记录](docs/verification.md)
