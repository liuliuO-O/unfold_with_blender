import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtGui import QPixmap
from pdf2image import convert_from_path
import subprocess
import os

class OpenGL3DView(QOpenGLWidget):
    def __init__(self, parent=None):
        super(OpenGL3DView, self).__init__(parent)
        self.vertices = []
        self.faces = []
        self.angle_x = 0
        self.angle_y = 0
        self.zoom = -3.0
        self.last_mouse_pos = None

    def load_obj(self, filename):
        self.vertices = []
        self.faces = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.strip().split()
                    vertex = list(map(float, parts[1:4]))
                    self.vertices.append(vertex)
                elif line.startswith('f '):
                    parts = line.strip().split()
                    face = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                    self.faces.append(face)
        self.vertices = self.center_and_scale(self.vertices)
        self.update()

    def center_and_scale(self, vertices):
        v = np.array(vertices)
        center = v.mean(axis=0)
        scale = np.max(v.max(axis=0) - v.min(axis=0))
        v = (v - center) / (scale * 0.5)
        return v.tolist()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glClearColor(0.1, 0.1, 0.1, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.zoom)
        glRotatef(self.angle_x, 1, 0, 0)
        glRotatef(self.angle_y, 0, 1, 0)
        self.draw_axes()
        self.draw_model()

    def draw_axes(self):
        glBegin(GL_LINES)
        # X - red
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)
        # Y - green
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 1, 0)
        # Z - blue
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1)
        glEnd()

    def draw_model(self):
        if not self.vertices or not self.faces:
            return
        # 1. 先正常绘制面
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for i in range(1, len(face) - 1):
                v0 = np.array(self.vertices[face[0]])
                v1 = np.array(self.vertices[face[i]])
                v2 = np.array(self.vertices[face[i + 1]])
                normal = np.cross(v1 - v0, v2 - v0)
                norm = np.linalg.norm(normal)
                if norm != 0:
                    normal = normal / norm
                else:
                    normal = [0, 0, 1]
                glNormal3fv(normal)
                glVertex3fv(self.vertices[face[0]])
                glVertex3fv(self.vertices[face[i]])
                glVertex3fv(self.vertices[face[i + 1]])
        glEnd()

        # 2. 再用线框模式画边
        glColor3f(0, 0, 0)  # 黑色边
        glLineWidth(2)      # 边宽度
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for i in range(1, len(face) - 1):
                v0 = np.array(self.vertices[face[0]])
                v1 = np.array(self.vertices[face[i]])
                v2 = np.array(self.vertices[face[i + 1]])
                normal = np.cross(v1 - v0, v2 - v0)
                norm = np.linalg.norm(normal)
                if norm != 0:
                    normal = normal / norm
                else:
                    normal = [0, 0, 1]
                glNormal3fv(normal)
                glVertex3fv(self.vertices[face[0]])
                glVertex3fv(self.vertices[face[i]])
                glVertex3fv(self.vertices[face[i + 1]])
        glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)  # 恢复填充模式

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            self.angle_x += dy
            self.angle_y += dx
            self.last_mouse_pos = event.pos()
            self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        self.zoom += delta * 0.2
        self.update()


class Canvas2DView(QWidget):
    def __init__(self, parent=None):
        super(Canvas2DView, self).__init__(parent)
        self.setMinimumWidth(400)
        self.image = None
        self.scale = 1.0  # 新增：缩放比例

    def load_pdf_image(self, pdf_path):
        poppler_path = r'E:\python_package\poppler-24.08.0\Library\bin'
        images = convert_from_path(pdf_path, dpi=150, poppler_path=poppler_path)
        if images:
            from PIL.ImageQt import ImageQt
            pil_image = images[0].convert("RGBA")
            qt_image = ImageQt(pil_image)
            if hasattr(qt_image, 'copy'):
                self.image = QPixmap.fromImage(qt_image.copy())
            else:
                self.image = QPixmap.fromImage(qt_image)
            self.scale = 1.0  # 加载新图片时重置缩放
            self.update()

    def wheelEvent(self, event):
        # 鼠标滚轮缩放
        delta = event.angleDelta().y() / 120
        factor = 1.1 if delta > 0 else 0.9
        self.scale *= factor
        self.scale = max(0.1, min(self.scale, 10))  # 限制缩放范围
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        if self.image:
            # 按缩放比例绘制图片，并居中
            scaled = self.image.scaled(
                int(self.image.width() * self.scale),
                int(self.image.height() * self.scale),
                aspectRatioMode=1
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(QColor(50, 50, 50))
            painter.drawText(20, 20, "2D 展开视图区域（待开发）")


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("3D + 2D 展示窗口")
        self.resize(1000, 600)

        # 创建两个视图
        self.gl_view = OpenGL3DView()
        self.canvas_view = Canvas2DView()

        # 设置布局
        layout = QHBoxLayout()
        layout.addWidget(self.gl_view, 1)
        layout.addWidget(self.canvas_view, 1)

        # 设置中央窗口
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 自动加载OBJ（也可以用菜单或按钮）
        obj_file, _ = QFileDialog.getOpenFileName(self, "打开OBJ文件", "", "OBJ Files (*.obj)")
        if obj_file:
            self.gl_view.load_obj(obj_file)

            script_path = os.path.join(os.path.dirname(__file__), "unfold_operator.py")
            subprocess.run([
                "blender",
                "--background", "--python", script_path, "--", obj_file
            ], cwd=os.path.dirname(__file__))

            # 2. 加载PDF图片
            pdf_file = obj_file.replace(".obj", "_unfold.pdf")
            self.canvas_view.load_pdf_image(pdf_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())