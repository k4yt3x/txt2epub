# TXT2EPUB

[中文说明](README.zh.md)

A simple tool for converting TXT books into [EPUB](https://en.wikipedia.org/wiki/EPUB).

![Image](https://github.com/user-attachments/assets/836e0c03-5fb9-42ab-883c-2fd80f6c1cd3)

## Installation

You'll first need to have Python3 and Pip installed. If you're using Windows, then the default Python installer will come with Pip. If you're using Linux, you may need to install an extra package like `python3-pip`. The exact package name depends on your distro.

Then, execute the following command to install TXT2EPUB.

```shell
pip install txt2epub
```

## Usage

You may convert a file from the command line:

```shell
txt2epub convert -i <input> -o <output> -t <title> -a <author> -l <language> -c <cover>
```

...or using the GUI:

```shell
txt2epub gui
```

## Chapter Detection

This program detects the book chapters and chapter titles following the standard TXT book format:

- Chapters are separated by three new lines (i.e., `\n\n\n`)
- The first line in a new chapter is the chapter's title.

For example, in the text below, there are two chapters with titles "Chapter 1" and "Chapter 2."

```txt
Chapter 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at sapien ante.

Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae.


Chapter 2

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at sapien ante.

Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae.
```
