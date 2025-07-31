import bpy
import bmesh
import sys
from mathutils import Vector
from math import pi, ceil

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unfold import Unfolder, UnfoldError
from pdf import Pdf

# 命令行参数处理
argv = sys.argv
argv = argv[argv.index("--") + 1:]
obj_file = argv[0]
print("Processing:", obj_file)

# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入 OBJ
bpy.ops.wm.obj_import(filepath=obj_file)
obj = bpy.context.selected_objects[0]

# 进入编辑模式并做基础清理
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles()
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.mesh.normals_make_consistent()


# 参数设置
cage_size = Vector((0.210, 0.297))  # A4 尺寸，单位米
priority_effect = {
    'CONVEX': 0.5,
    'CONCAVE': 1,
    'LENGTH': -0.05,
}

class ExportProps:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.directory = os.path.dirname(filepath)
        self.page_size_preset = 'A4'
        self.output_size_x = 0.210
        self.output_size_y = 0.297
        self.output_margin = 0.005
        self.texture_type = 'NONE'
        self.output_layers = 'ONESIDE'
        self.do_create_stickers = False
        self.do_create_numbers = True
        self.sticker_width = 0.005
        self.angle_epsilon = pi / 360
        self.output_dpi = 90
        self.bake_samples = 64
        self.file_format = 'PDF'
        self.image_packing = 'ISLAND_EMBED'
        self.nesting_method = 'BOX'
        self.scale = 1.0
        self.do_create_uvmap = True
        self.scale_length = 1.0
        self.use_auto_scale = 1

        # style属性
        class DummyStyle:
            def __init__(self):
                # 可选的线条样式
                self.line_styles = [
                    ('SOLID', "Solid (----)", "Solid line"),
                    ('DOT', "Dots (. . .)", "Dotted line"),
                    ('DASH', "Short Dashes (- - -)", "Solid line"),
                    ('LONGDASH', "Long Dashes (-- --)", "Solid line"),
                    ('DASHDOT', "Dash-dotted (-- .)", "Solid line")
                ]

                # 外轮廓线设置
                self.outer_color = (0.0, 0.0, 0.0, 1.0)    # 颜色 RGBA
                self.outer_style = 'SOLID'                # 线型
                self.line_width = 1e-4                    # 线宽（米）
                self.outer_width = 3                      # 外轮廓线相对粗细倍数
                self.use_outbg = True                     # 是否加高亮背景
                self.outbg_color = (1.0, 1.0, 1.0, 1.0)   # 高亮背景颜色
                self.outbg_width = 5                      # 高亮背景线粗细倍数

                # 内部凸折线
                self.convex_color = (0.0, 0.0, 0.0, 1.0)  # 内部凸折线颜色
                self.convex_style = 'DASH'                # 内部凸折线样式
                self.convex_width = 2                     # 相对粗细

                # 内部凹折线
                self.concave_color = (0.0, 0.0, 0.0, 1.0)
                self.concave_style = 'DASHDOT'
                self.concave_width = 2

                # 自定义 Freestyle 边
                self.freestyle_color = (0.0, 0.0, 0.0, 1.0)
                self.freestyle_style = 'SOLID'
                self.freestyle_width = 2

                # 内部高亮
                self.use_inbg = True
                self.inbg_color = (1.0, 1.0, 1.0, 1.0)
                self.inbg_width = 2

                # 标签和文字颜色
                self.sticker_color = (0.9, 0.9, 0.9, 1.0)
                self.text_color = (0.0, 0.0, 0.0, 1.0)

        self.style = DummyStyle()

def get_scale_ratio(unfolder,export_props):
    margin = export_props.output_margin + export_props.sticker_width
    if min(export_props.output_size_x, export_props.output_size_y) <= 2 * margin:
        return False
    output_inner_size = Vector((export_props.output_size_x - 2*margin, export_props.output_size_y - 2*margin))
    ratio = unfolder.mesh.largest_island_ratio(output_inner_size)
    return ratio * export_props.scale_length / export_props.scale

def prepare(obj,export_props):
    unfolder = Unfolder(obj)
    cage_size = Vector((export_props.output_size_x, export_props.output_size_y))
    unfolder_scale = export_props.scale_length/export_props.scale                                                                
    unfolder.prepare(cage_size, scale=unfolder_scale)
    if export_props.use_auto_scale:               
        export_props.scale = ceil(get_scale_ratio(unfolder,export_props))
    return unfolder

def main():
    try:
        pdf_file = obj_file.replace(".obj", "_unfold.pdf")
        export_props = ExportProps(pdf_file)
        unfolder = prepare(obj, export_props)
        exporter_class = Pdf
        exporter = exporter_class(export_props)
        output_file = unfolder.save(export_props, exporter)
        print("Saved a {}-page document".format(len(unfolder.mesh.pages)))
    except UnfoldError as error:
        print("ERROR_INVALID_INPUT:", error.args[0])

if __name__ == "__main__":
    main()