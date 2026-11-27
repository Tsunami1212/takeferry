# 镜渡 TakeFerry

[English](README.md)

把一场戏贴进 Hermes，确认分镜，先挑一个镜头。镜渡帮你写提示词、选模型，通过 MCP 在 LibTV 或小云雀的原生画布上搭工作流。参考图可以分别管人物、灯光或机位。你确认之后才进入相应平台的生成步骤，积分由该平台账号承担。

想把固定机位换成慢推，就从选中的候选另做一版。想看另一家怎样处理同一个镜头，就沿用原来的拍法和要求。每条候选保留各自的画布、节点、父版本与回执。值得复用的方法可以存回自己的 Hermes Skill。

## 本地试一遍

从代码目录运行以下命令，需要 Python 3.9 或以上。也可以下载发行页的 `takeferry.pyz`，运行 `python3 takeferry.pyz demo --output rainy-door-demo`。

```sh
python3 -m takeferry demo --output rainy-door-demo
```

在输出目录打开 `rain-at-the-door.zip`。里面有被采用的五秒原片和标了入出点的剪辑清单。两个画布快照、四条候选的制作记录，以及供 Hermes 保存的技能草稿都在同一目录。示例使用随包提供的手绘分镜和模拟平台回执，运行全程离线，消耗零平台积分。

接入真实账号请看 [Hermes 配置](docs/setup.md)。LibTV 通过官方 Remote MCP 操作，小云雀通过镜渡的 MCP 适配器调用官方 Canvas CLI。此公开版本尚未进行双平台付费实拍。[验证状态](docs/verification.md) · [版本下载](https://github.com/Tsunami1212/takeferry/releases/tag/v0.1.0-alpha.1)
