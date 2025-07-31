import bpy
import bmesh
import sys
from mathutils import Vector

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ============ 处理命令行参数 ============
argv = sys.argv
argv = argv[argv.index("--") + 1:]
obj_file = argv[0]
print("Processing:", obj_file)

# ============ 清空场景 ============
bpy.ops.wm.read_factory_settings(use_empty=True)

# ============ 导入 OBJ ============
bpy.ops.wm.obj_import(filepath=obj_file)
obj = bpy.context.selected_objects[0]

# ============ 切换到 Edit 模式 ============
bpy.context.view_layer.objects.active = obj

obj.select_set(True)

bpy.ops.object.mode_set(mode='EDIT')

# 全选
bpy.ops.mesh.select_all(action='SELECT')

# 清理重顶点
bpy.ops.mesh.remove_doubles()

# 三角化
bpy.ops.mesh.quads_convert_to_tris()

# 法线统一
bpy.ops.mesh.normals_make_consistent()

# ============ 调用 Unfolder 逻辑 ============
# 假设你的 Unfolder 类可以直接 import
from unfold import Unfolder, UnfoldError  # 你已有的类

# 模拟你的参数
sce = bpy.context.scene
# 这里根据你插件的需要设置参数
cage_size = Vector((200, 200))
priority_effect = {
    'CONVEX': 0.5,  # 你可以替换成实际方法
    'CONCAVE': 1,
    'LENGTH': -0.05,
}

try:
    unfolder = Unfolder(obj)
    unfolder.do_create_uvmap = True
    scale = 1.0
    unfolder.prepare(cage_size, priority_effect, scale, False)
    unfolder.mesh.mark_cuts()
except UnfoldError as error:
    print("Unfold failed:", error)
    bpy.ops.wm.quit_blender()
    raise

# 如果需要访问展开结果，可以访问 unfolder.mesh.islands
print("Unfold islands:", len(unfolder.mesh.islands))

# ============ 保存结果或导出 ============
# 例如导出为新 obj
# output_path = obj_file.replace(".obj", "_unfolded.obj")
# bpy.ops.export_scene.obj(filepath=output_path)

# ============ 退出 Blender ============
bpy.ops.wm.quit_blender()