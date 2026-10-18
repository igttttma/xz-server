# Voice Box Theme Customization

## Project Overview

This directory contains the static files bundled from the [xiaozhi-assets-generator](https://github.com/xinnan-tech/xiaozhi-assets-generator) project, used for customizing and generating voice box themes online. With this tool, users can configure elements such as the wake word, font, emoji and chat background, and export them as an `assets.bin` file.

## Directory Structure

```
generator/
├── assets/              # Build output resources
│   ├── ft_render-ByO_jG18.js
│   ├── index-CYcyz9xb.js
│   └── index-NXxBVrod.css
├── static/              # Static resource directory
│   ├── charsets/        # Charset files
│   │   ├── deepseek.txt
│   │   ├── gb2312.txt
│   │   ├── latin1.txt
│   │   └── qwen18409.txt
│   ├── fonts/           # Font resources
│   │   ├── font_noto_qwen_14_1.bin
│   │   ├── font_noto_qwen_16_4.bin
│   │   ├── font_noto_qwen_20_4.bin
│   │   ├── font_noto_qwen_30_4.bin
│   │   ├── font_puhui_deepseek_14_1.bin
│   │   ├── font_puhui_deepseek_16_4.bin
│   │   ├── font_puhui_deepseek_20_4.bin
│   │   ├── font_puhui_deepseek_30_4.bin
│   │   ├── noto_qwen.ttf
│   │   └── puhui_deepseek.ttf
│   ├── multinet_model/  # Custom wake word models
│   │   ├── fst/
│   │   ├── mn6_cn/
│   │   ├── mn6_en/
│   │   ├── mn7_cn/
│   │   └── mn7_en/
│   ├── twemoji32/       # 32x32 emoji images
│   ├── twemoji64/       # 64x64 emoji images
│   ├── wakenet_model/   # Preset wake word models
│   └── README.md        # Static resource documentation
├── index.html           # Main page
└── README.md            # Project documentation
```

## Key Features

### 1. Chip and Screen Configuration
- Supports multiple chip models: ESP32-S3, ESP32-C3, ESP32-P4, ESP32-C6
- Flexible screen resolution settings
- Supports the RGB565 color format

### 2. Wake Word Configuration
- **Preset wake words**: based on the WakeNet models supported by each chip
- **Custom wake words**: supports Chinese and English command words, with configurable threshold and timeout

### 3. Font Configuration
- Several preset fonts: Alibaba PuHuiTi, Noto Qwen, and more
- Supports uploading custom TTF/WOFF font files
- Configurable font size and color depth (bpp)

### 4. Emoji Set
- Provides a preset set of 21 basic emoji (in both 32x32 and 64x64 sizes)
- Supports uploading custom emoji

### 5. Chat Background
- Supports switching between light and dark modes
- Configurable solid color or image background
- Automatically adapts to the screen resolution

## Usage

1. Serve the `index.html` file over HTTP
2. Select the chip model and screen configuration
3. Configure the theme elements through the various tabs
4. Click the generate button to review the resource manifest
5. Confirm to generate and download the `assets.bin` file

## Technical Notes

- The built static resources are located in the `assets/` directory
- The original models and resource files are located in the `static/` directory
- Works offline, with no additional dependencies

## Notes

- This tool is designed for offline use; all resources are already included in the directory
- The generated `assets.bin` file must be used together with the voice box hardware
- Custom resources must respect the file format and size limits to ensure compatibility
