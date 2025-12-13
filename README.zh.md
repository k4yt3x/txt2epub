# TXT2EPUB

一个简单的 TXT 到 [EPUB](https://en.wikipedia.org/wiki/EPUB) 书籍转换工具。

![Image](https://github.com/user-attachments/assets/836e0c03-5fb9-42ab-883c-2fd80f6c1cd3)

## 安装

首先您需要装有 Python3 和 Pip。如果您使用的是 Windows，那么 Python 安装会默认带 Pip。如果您使用的是 Linux，那么您可能需要额外安装 `python3-pip` 之类的包，具体的名称取决于您的发行版。

执行以下命令以安装 TXT2EPUB：

```shell
pip install txt2epub
```

## 使用

您可以直接在命令行里运行：

```shell
txt2epub convert -i <输入文件> -o <输出文件> -t <书名> -a <作者> -l <语言> -c <封面>
```

……或者运行图形化界面：

```shell
txt2epub gui
```

## 章节检测

该程序按照标准的 TXT 书籍格式检测书籍的章节和章节标题：

- 章节之间由三个 LF 换行符（即，`\n\n\n`）分隔
- 新章节的第一行是章节的标题。

例如，在下面的文本中，有两个章节，标题分别为 "Chapter 1" 和 "Chapter 2"。

```txt
Chapter 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at sapien ante.

Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae.


Chapter 2

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at sapien ante.

Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae.
```
