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

The tool now detects chapters in two ways:

- Heading-based: lines that look like chapter titles are treated as chapter starts (e.g. `Chapter 3`, `CHAPTER V`, `Section 10`).
- Fallback: if no headings are found, chapters are split by three new lines (`\n\n\n`), with the first line of each block used as the title.
