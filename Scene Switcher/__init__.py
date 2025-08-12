bl_info = {
    "name": "Scene Switcher Pie",
    "author": "Binz1 Animation",
    "version": (1, 0),
    "blender": (2, 8)
    "location": "Shortcut Key",
    "description": "Pie menu to switch scenes",
    "category": "Scene",
}

import bpy

addon_keymap = []
scene_offset = 0

class SCENE_OT_switch(bpy.types.Operator):
    bl_idname = "scene.switch_scene"
    bl_label = "Switch Scene"
    bl_description = "Switch to selected scene"
    scene_name: bpy.props.StringProperty()

    def execute(self, context):
        if self.scene_name in bpy.data.scenes:
            context.window.scene = bpy.data.scenes[self.scene_name]
            self.report({'INFO'}, f"Switched to scene: {self.scene_name}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Scene not found")
            return {'CANCELLED'}

class SCENE_OT_next_page(bpy.types.Operator):
    bl_idname = "scene.next_page"
    bl_label = "Next Page"
    bl_description = "Go to next page"

    def execute(self, context):
        global scene_offset
        scenes_count = len(bpy.data.scenes)
        scene_offset += 7
        if scene_offset >= scenes_count:
            scene_offset = 0
        bpy.ops.wm.call_menu_pie(name="SCENE_MT_pie_menu")
        return {'FINISHED'}

class SCENE_OT_prev_page(bpy.types.Operator):
    bl_idname = "scene.prev_page"
    bl_label = "Previous Page"
    bl_description = "Go to previous page"

    def execute(self, context):
        global scene_offset
        scenes_count = len(bpy.data.scenes)
        scene_offset -= 7
        if scene_offset < 0:
            scene_offset = 0
        bpy.ops.wm.call_menu_pie(name="SCENE_MT_pie_menu")
        return {'FINISHED'}

class SCENE_MT_pie_menu(bpy.types.Menu):
    bl_label = "Switch Scene Pie Menu"

    def draw(self, context):
        global scene_offset
        layout = self.layout
        pie = layout.menu_pie()
        scenes = sorted(bpy.data.scenes, key=lambda s: s.name.lower())
        scenes_count = len(scenes)

        max_slots = 8
        max_scenes_per_page = 7

        if scenes_count <= max_slots:
            for scene in scenes:
                op = pie.operator("scene.switch_scene", text=scene.name)
                op.scene_name = scene.name
            return

        end = scene_offset + max_scenes_per_page
        displayed_scenes = scenes[scene_offset:end]

        has_prev = scene_offset > 0
        has_next = end < scenes_count

        nav_buttons = (1 if has_prev else 0) + (1 if has_next else 0)
        num_scene_slots = max_slots - nav_buttons

        if has_prev:
            pie.operator("scene.prev_page", text="◀ Prev")

        for scene in displayed_scenes[:num_scene_slots]:
            op = pie.operator("scene.switch_scene", text=scene.name)
            op.scene_name = scene.name

        if has_next:
            pie.operator("scene.next_page", text="Next ▶")

class SceneSwitcherSettings(bpy.types.PropertyGroup):
    key: bpy.props.StringProperty(name="Key", default="E")
    ctrl: bpy.props.BoolProperty(name="Ctrl", default=False)
    alt: bpy.props.BoolProperty(name="Alt", default=False)
    shift: bpy.props.BoolProperty(name="Shift", default=False)
    capturing: bpy.props.BoolProperty(name="Capturing", default=False)

def unregister_shortcut():
    global addon_keymap
    for km, kmi in addon_keymap:
        km.keymap_items.remove(kmi)
    addon_keymap.clear()

def register_shortcut(context=None):
    unregister_shortcut()

    key = "E"
    ctrl = False
    alt = False
    shift = False

    if context is not None:
        prefs = getattr(context.scene, "scene_switcher_settings", None)
        if prefs:
            key = prefs.key.upper()
            ctrl = prefs.ctrl
            alt = prefs.alt
            shift = prefs.shift

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km.keymap_items.new('wm.call_menu_pie', key, 'PRESS')
    kmi.properties.name = "SCENE_MT_pie_menu"
    kmi.ctrl = ctrl
    kmi.alt = alt
    kmi.shift = shift
    addon_keymap.append((km, kmi))

class SCENE_OT_start_capture(bpy.types.Operator):
    bl_idname = "scene_switcher.start_capture"
    bl_label = "Press a key"

    def modal(self, context, event):
        prefs = context.scene.scene_switcher_settings
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            prefs.capturing = False
            self.report({'INFO'}, "Shortcut capture canceled")
            return {'CANCELLED'}

        if event.value == 'PRESS':
            if event.type in {'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_ALT', 'RIGHT_ALT', 'LEFT_SHIFT', 'RIGHT_SHIFT'}:
                return {'RUNNING_MODAL'}

            prefs.key = event.unicode.upper() if event.unicode else event.type
            prefs.ctrl = event.ctrl
            prefs.alt = event.alt
            prefs.shift = event.shift
            prefs.capturing = False
            self.report({'INFO'}, f"Shortcut set to: {'Ctrl+' if prefs.ctrl else ''}{'Alt+' if prefs.alt else ''}{'Shift+' if prefs.shift else ''}{prefs.key}")
            register_shortcut(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        prefs = context.scene.scene_switcher_settings
        if prefs.capturing:
            return {'CANCELLED'}
        prefs.capturing = True
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Press a key for shortcut, right-click or ESC to cancel")
        return {'RUNNING_MODAL'}

classes = (
    SCENE_OT_switch,
    SCENE_OT_next_page,
    SCENE_OT_prev_page,
    SCENE_MT_pie_menu,
    SceneSwitcherSettings,
    SCENE_OT_start_capture,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.scene_switcher_settings = bpy.props.PointerProperty(type=SceneSwitcherSettings)
    register_shortcut()

def unregister():
    unregister_shortcut()
    del bpy.types.Scene.scene_switcher_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
