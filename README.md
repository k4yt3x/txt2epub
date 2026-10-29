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

### Combining multiple TXT files

Use **Select Files** to select several TXT files, or drag and drop them together.
They are sorted naturally by filename (`1`, `2`, `10`) and combined into one EPUB,
with exactly one chapter per file. The first nonblank line becomes the chapter
title and is removed from the body to avoid duplication. Empty files use their
filename as the title. UTF-8 files with or without a BOM are supported.

Chapter detection controls apply only to single-file conversion. For multiple
files, choose the output location when generating the EPUB. Hover over the selected
files message to see their order.

Missing internal filename numbers are reported before conversion in the GUI and
as warnings in the CLI. Numbers are compared among filenames with the same text
before the number; titles after it may differ. For example, `Book_001_First.txt`
and `Book_003_New beginning.txt` report `2`.
Different prefixes are checked separately; missing numbers before the first
or after the last selected number cannot be inferred. Warnings do not block conversion.

```shell
txt2epub convert -i book_001.txt book_002.txt book_003.txt -o combined.epub
```

Without `-o`, multiple inputs produce `<first-file-stem>_combined.epub` beside the
first file in sorted order. Single-file output naming remains unchanged.

### Single-file chapter detection

Chapter detection is enabled by default. To disable it, select **No chapters**
in the GUI, or add `--no-chapters` on the command line:

```shell
txt2epub convert -i book.txt --no-chapters
```

With detection disabled, all lines (including the first line) remain body text in
one continuous section, without generated chapter headings. EPUB navigation
contains a single entry using the book title.

For numbered headings such as `# 1` and `# 2001`, select **Number chapters** in the
GUI or use `txt2epub convert -i book.txt --number-chapters`. Each heading must be
on its own line: `#`, one space, and ASCII digits. Leading and trailing spaces
or tabs are allowed, so ` # 2` is also recognized.
Select **Custom chapters** to reveal an editable **Chapter regex** field.
The default pattern recognizes Korean episode headings such as `877화. 혈식`.
Enter a Python regular expression matching the entire title line, for example
`Chapter [0-9]+: .+`. Leading/trailing spaces and tabs are removed for matching,
and blank lines are never treated as headings. The complete matching line becomes
the chapter title; capture groups do not change it. Matching is per line, so
multiline headings are not supported. Empty or invalid patterns stop conversion.
To recognize both formats, use `(?:# [0-9]+|[0-9]+화\.[ \t]+.+)`.

```shell
txt2epub convert -i book.txt --custom-chapters --chapter-pattern 'Chapter [0-9]+: .+'
```

`--chapter-pattern` requires `--custom-chapters`. Omitting the pattern keeps the
default Korean episode format. Other chapter modes ignore the GUI regex field.
`--number-chapters`, `--custom-chapters`, and `--no-chapters` are mutually exclusive.
Surrounding blank lines and decorative
lines such as `*` or `-` are preserved as body text and are not required for detection.
The heading becomes the chapter title and each chapter is stored separately in
the EPUB. Blank lines within a chapter do not split it. Text before the first
heading is preserved as an opening section named after the book. If no headings
match, all text is kept as one body section. This option cannot be combined with
`--no-chapters`.

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
