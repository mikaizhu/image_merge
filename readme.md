# 软件说明
这是一款图片拼接软件，支持图片水平拼接，windows only！
该软件支持：
1. 本地上传图片进行拼接
2. 支持从剪贴板中copy图片拼接
3. 支持将拼接的图片保存到本地和保存到剪贴板中
4. 上传的图片预览，和清空
5. 操作撤销undo功能，但是目前没有做undo undo的功能，所以慎用undo

# 记录下自己踩的坑
坑：打包成exe文件时，报错no module pillow 或者 win32clipboard
主要原因：环境不对，windows下vscode中切换python环境切换不了，但是又不会报错，导致pyinstaller打包会丢失模块

# 如果缺失模块怎么处理

建议安装：
1. auto-py-to-exe: https://github.com/brentvollebregt/auto-py-to-exe/blob/master/README-Chinese.md
2. pyinstaller

如何让exe文件小一些？

打开cmd，使用conda环境的话，就conda activate下对应环境，然后在这个环境中把需要的模块安装了

如何打包成exe？

在auto py to exe界面中，选择主程序文件，比如我的是app_v1.0.py，选择好后可以选择单文件打包，或者多文件打包，再选择ico格式的图标即可

多文件打包或者单文件打包，确实了模块怎么办？

多文件打包可以测试缺少了哪些模块，然后统一安装，比如缺少了pillow模块，那么可以拷贝整个pillow库

\miniconda3\envs\py\Lib\site-packages\pillow

到目录下面:~\output\app_v1.0\_internal (可以在py to exe中打开文件夹)

单文件打包，就把这个文件，弄到addtional file下面
