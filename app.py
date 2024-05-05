import tkinter as tk
from tkinter import Tk, Menu
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps, ImageGrab
import io
from io import BytesIO
import win32clipboard
import win32con


class ImageMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Viewer and Merger")
        self.images = []
        self.raw_images = []  # 存储原始尺寸图片的列表
        self.history = []
        self.undo_history = []
        self.current_preview_index = None
        self.preview_window = None
        self.show_success_message = True  # 默认显示成功消息

        self.upload_btn = ttk.Button(root, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(fill=tk.X)

        self.copy_btn = ttk.Button(root, text="Copy merged image", command=self.copy_merged_to_clipboard)
        self.copy_btn.pack(fill=tk.X)

        self.paste_btn = ttk.Button(root, text="Paste Image from Clipboard", command=self.paste_from_clipboard)
        self.paste_btn.pack(fill=tk.X)

        self.save_btn = ttk.Button(root, text="Save merged image", command=self.save_merged_image)
        self.save_btn.pack(fill=tk.X)

        self.clear_btn = ttk.Button(root, text="Clear All Images", command=self.clear_all_images)
        self.clear_btn.pack(fill=tk.X)

        self.undo_btn = ttk.Button(root, text="Undo", command=self.undo_last_action)
        self.undo_btn.pack(fill=tk.X)

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(root, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.canvas_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor='nw')

        self.canvas_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self.mouse_wheel)
        # 绑定 Ctrl+V 快捷键
        self.root.bind("<Control-v>", self.paste_from_clipboard_event)

    def upload_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.load_image(file_path)
            self.undo_history.append(('add', len(self.raw_images) - 1))  # 记录这是添加操作


    # 修改粘贴函数，以适应事件调用
    def paste_from_clipboard_event(self, event):
        try:
            # 尝试从剪贴板获取图片
            img = ImageGrab.grabclipboard()
            if img:
                self.raw_images.append(img)
                self.display_thumbnail(img)
                self.undo_history.append(('add', len(self.raw_images) - 1))  # 记录这是添加操作
            else:
                messagebox.showerror("Error", "No image in clipboard!")
        except Exception as e:
            messagebox.showerror("Error", "Failed to paste image from clipboard: " + str(e))

    def paste_from_clipboard(self):
        try:
            # 尝试从剪贴板获取图片
            img = ImageGrab.grabclipboard()
            if img:
                self.raw_images.append(img)
                self.display_thumbnail(img)
                self.undo_history.append(('add', len(self.raw_images) - 1))  # 记录这是添加操作
            else:
                messagebox.showerror("Error", "No image in clipboard!")
        except Exception as e:
            messagebox.showerror("Error", "Failed to paste image from clipboard: " + str(e))

    def load_image(self, file_path):
        original_img = Image.open(file_path)
        self.raw_images.append(original_img.copy())  # 保存原始图片
        self.display_thumbnail(original_img)

    def display_thumbnail(self, img):
        thumbnail_img = img.copy()
        thumbnail_img.thumbnail((100, 100), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(thumbnail_img)
        label = ttk.Label(self.canvas_frame, image=photo)
        label.image = photo
        label.pack()
        label.bind("<Double-Button-1>", lambda e, idx=len(self.images): self.preview_image(idx))
        label.bind("<Button-3>", lambda e, idx=len(self.images): self.popup_menu(e, idx))
        self.images.append(thumbnail_img)
        self.history.append((thumbnail_img, label))

    def popup_menu(self, event, index):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Delete", command=lambda: self.delete_image(index))
        menu.post(event.x_root, event.y_root)

    def delete_image(self, index):
        # 检查索引是否在有效范围内
        if index >= 0 and index < len(self.raw_images):
            # 从列表中移除图片和对应的标签
            self.undo_history.append(('delete', index, self.raw_images[index]))  # 记录删除操作及其详细信息
            self.images.pop(index)
            self.raw_images.pop(index)
            label_to_remove = self.history.pop(index)[1]
            label_to_remove.destroy()
            
            # 更新后续所有图片的绑定事件，以确保索引正确
            for idx, (_, label) in enumerate(self.history[index:], start=index):
                label.bind("<Double-Button-1>", lambda e, idx=idx: self.preview_image(idx))
                label.bind("<Button-3>", lambda e, idx=idx: self.popup_menu(e, idx))
        else:
            messagebox.showerror("Error", "Invalid image index")

    def preview_image(self, index):
        preview_width, preview_height = 800, 600  # 设置预览窗口的大小
        original_img = self.raw_images[index]
        
        # 根据图片大小调整显示方式
        if original_img.width > preview_width or original_img.height > preview_height:
            # 缩放图片
            img_resized = ImageOps.contain(original_img, (preview_width, preview_height))
        else:
            # 正常展示图片
            img_resized = original_img

        photo = ImageTk.PhotoImage(img_resized)

        if self.preview_window is None or not tk.Toplevel.winfo_exists(self.preview_window):
            self.preview_window = tk.Toplevel(self.root)
            self.preview_window.title("Image Preview")
            self.preview_window.geometry(f"{preview_width}x{preview_height + 50}")  # 增加窗口高度以容纳按钮

            self.preview_frame = tk.Frame(self.preview_window)
            self.preview_frame.pack(fill=tk.BOTH, expand=True)

            # 图片展示Label
            self.photo_label = tk.Label(self.preview_frame)
            self.photo_label.pack(expand=True)

            # 按钮容器
            button_frame = tk.Frame(self.preview_window)
            button_frame.pack(fill=tk.X)

            # 添加控制按钮
            self.previous_button = tk.Button(button_frame, text="Previous", width=20, padx=10, pady=10, command=lambda: self.change_preview(-1))
            self.previous_button.pack(side=tk.LEFT, padx=10, pady=10)

            self.next_button = tk.Button(button_frame, text="Next", width=20, padx=10, pady=10, command=lambda: self.change_preview(1))
            self.next_button.pack(side=tk.RIGHT, padx=10, pady=10)
        else:
            self.preview_window.focus_set()

        self.photo_label.config(image=photo)
        self.photo_label.image = photo
        self.current_preview_index = index

    def change_preview(self, direction):
        new_index = (self.current_preview_index + direction) % len(self.raw_images)
        self.preview_image(new_index)

    def change_preview(self, direction):
        # 计算新的图片索引
        new_index = (self.current_preview_index + direction) % len(self.raw_images)
        self.preview_image(new_index)

    def change_preview(self, direction):
        new_index = (self.current_preview_index + direction) % len(self.raw_images)
        self.preview_image(new_index)

    def clear_all_images(self):
        # 清除所有图片
        self.undo_history.append(('clear', list(self.raw_images)))  # 记录清空操作及所有图片
        self.images.clear()
        self.raw_images.clear()
        for _, label in self.history:
            label.destroy()
        self.history.clear()

    def merge_images(self):
        if not self.raw_images:
            messagebox.showerror("Error", "No images to merge")
            return

        # 初始化合并后的图像大小
        total_width = max(img.width for img in self.raw_images)
        total_height = sum(img.height for img in self.raw_images)

        # 创建一个新的空白图像，大小足以容纳所有垂直拼接的图像
        merged_image = Image.new('RGB', (total_width, total_height))

        current_y = 0  # 当前y坐标（垂直偏移）
        for img in self.raw_images:
            if img.width < total_width:
                # 创建一个宽度为最大宽度的灰色背景图像
                temp_img = Image.new('RGB', (total_width, img.height), (192, 192, 192))
                temp_img.paste(img, (0, 0))  # 将原图粘贴到灰色背景图的左上角
                img = temp_img  # 更新img为新的图像
            merged_image.paste(img, (0, current_y))
            current_y += img.height  # 更新y坐标

        return merged_image
    
    def copy_merged_to_clipboard(self):
        if self.raw_images:  # 确保有图片可供合并
            merged_image = self.merge_images()
            # 将图片保存到内存中的字节流对象
            output = BytesIO()
            merged_image.save(output, format='BMP')
            data = output.getvalue()[14:]  # BMP文件头需要被剔除
            
            # 打开剪贴板
            win32clipboard.OpenClipboard()
            # 清空剪贴板
            win32clipboard.EmptyClipboard()
            # 设置剪贴板数据
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            # 关闭剪贴板
            win32clipboard.CloseClipboard()
            
            if self.show_success_message:
                self.show_success_popup()

    def show_success_popup(self):
        response = messagebox.askyesno("Success", "Merged image copied to clipboard! Would you like to see this message in the future?")
        self.show_success_message = response
    
    def save_merged_image(self):
        merged_image = self.merge_images()
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
        if file_path:
            merged_image.save(file_path)

    def undo_last_action(self):
        if self.undo_history:
            action, *data = self.undo_history.pop()
            if action == 'add':
                index = data[0]
                self.delete_image(index)
            elif action == 'delete':
                index, img = data
                self.raw_images.insert(index, img)
                self.display_thumbnail(img)
            elif action == 'clear':
                for img in data[0]:
                    self.raw_images.append(img)
                    self.display_thumbnail(img)


    def mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

if __name__ == "__main__":
    root = Tk()
    app = ImageMergerApp(root)
    root.mainloop()


