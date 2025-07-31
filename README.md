# Unfold with blender

依赖 Blender 的 3D 模型展开工具，支持将 3D 模型的.obj格式自动展平并导出为 PDF/图片。

---

## 安装方法

## 注意事项

1. 安装blender并将blender添加至系统变量 E:\path\to\Blender 4.5\
2. 下载poppler，解压后记下bin目录路径，将obj_loader.py中poppler_path改为你的poppler bin路径

```bash
git https://github.com/liuliuO-O/unfold_with_blender.git
cd unfold_with_blender
python ./obj_loader.py
```

------

## 环境

- Windows 11
- Blender 4.5
- Python 3.10
- 第三方库缺啥pip啥

------

## 项目目录结构

```
Unfold with blender/
│  nesting.py               # 排版文件
│  obj_loader.py            # 图形化界面
│  pdf.py                   # 导出PDF逻辑
│  README.md
│  test.py                  # 连接blender测试文件
│  unfold.py                # 核心展开逻辑
│  unfold_operator.py       # 展开操作逻辑
│
├─obj                       # obj测试文件
└─pdf                       # pdf导出文件
```