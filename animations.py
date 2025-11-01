import bpy
import os

# مسیر فولدر انیمیشن‌ها
animations_folder = r"C:\Users\hp\Downloads\Animations\Animations\Animations"  # اینجا مسیر پوشه انیمیشن‌ها رو بزنید
output_file = r"C:\Users\hp\Downloads\Animations\Animations\Animations\animations.glb"  # خروجی دقیقا با همین اسم باشه

# پاک کردن همه چیز از صحنه
bpy.ops.wm.read_factory_settings(use_empty=True)

# ایمپورت کاراکتر اصلی (فقط برای گرفتن اسکلت/Armature)
character_path = r"C:\Users\hp\Downloads\Animations\Animations\Character Character DL From Main Character DL From Main Character DL From ReadyPlayerMe.glb"
bpy.ops.import_scene.gltf(filepath=character_path)

# فقط آرماتور رو نگه می‌داریم
for obj in bpy.context.scene.objects:
    if obj.type != "ARMATURE":
        bpy.data.objects.remove(obj, do_unlink=True)

# گرفتن آرماتور
armature = None
for obj in bpy.context.selected_objects:
    if obj.type == "ARMATURE":
        armature = obj
        break

if not armature:
    raise Exception("هیچ آرماتوری پیدا نشد!")

# وارد کردن همه فایل‌های انیمیشن و وصل کردن به همون آرماتور
for file in os.listdir(animations_folder):
    if file.lower().endswith((".fbx", ".glb", ".gltf")):
        anim_path = os.path.join(animations_folder, file)
        print(f"Importing animation: {anim_path}")
        if file.lower().endswith(".fbx"):
            bpy.ops.import_scene.fbx(
                filepath=anim_path, automatic_bone_orientation=True
            )
        else:
            bpy.ops.import_scene.gltf(filepath=anim_path)

        # اطمینان از ذخیره اکشن‌ها
        for action in bpy.data.actions:
            action.use_fake_user = True

# حالا فقط آرماتور + انیمیشن‌ها رو اکسپورت می‌کنیم
bpy.ops.export_scene.gltf(
    filepath=output_file,
    export_format="GLB",
    export_apply=True,
    use_selection=False,
    export_animations=True,
)

print(f"✅ animations.glb ساخته شد در: {output_file}")


import bpy
import os

# مسیر فایل کاراکتر اصلی/
character_path = "C:/Users/hp/Downloads/Animations/Animations/Character/main.glb"

# مسیر پوشه انیمیشن‌ها
animations_folder = "C:/Users/hp/Downloads/Animations/Animations/Animations"

# مسیر خروجی GLB
output_path = "C:/Users/hp/Downloads/Animations/Animations/Character/animations.glb"

# پاکسازی صحنه
bpy.ops.wm.read_factory_settings(use_empty=True)

# وارد کردن کاراکتر
bpy.ops.import_scene.gltf(filepath=character_path)
character = bpy.context.selected_objects[0]

# لیست فایل‌های fbx در پوشه
fbx_files = [f for f in os.listdir(animations_folder) if f.lower().endswith(".fbx")]

for fbx in fbx_files:
    fbx_path = os.path.join(animations_folder, fbx)
    print(f"Importing {fbx_path}")

    # وارد کردن fbx انیمیشن
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    # گرفتن اکشن انیمیشن
    for action in bpy.data.actions:
        if action.name not in character.animation_data.nla_tracks:
            track = character.animation_data.nla_tracks.new()
            strip = track.strips.new(action.name, 0, action)

# خروجی glb
bpy.ops.export_scene.gltf(
    filepath=output_path, export_format="GLB", use_selection=False
)
print("✅ Export finished:", output_path)
