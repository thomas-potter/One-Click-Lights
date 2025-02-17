import bpy
import os
from bpy.types import Panel, Operator
from bpy.props import StringProperty, CollectionProperty
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "OneClickLights",
    "author": "Potter3D",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),  # Minimum Blender version
    "location": "View3D > UI",
    "description": "One Click to Instantly Light your Scene",
}

# -------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------
def get_light_setups_data():
    """
    Scans the light_setups directory and returns a list of dictionaries,
    each containing the name (without extension) and the full path
    to the .blend file and the preview image.
    """
    addon_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Addon path: {addon_path}")  # Check the addon path
    light_setups_dir = os.path.join(addon_path, "light_setups")
    print(f"Light setups directory: {light_setups_dir}")  # Check the light setups directory
    previews_dir = os.path.join(addon_path, "previews")
    light_setups = []

    if not os.path.exists(light_setups_dir):
        os.makedirs(light_setups_dir)  # Create if it doesn't exist
        print(f"Created light_setups directory: {light_setups_dir}")
        return []  # Return empty list if just created

    try:
        for filename in os.listdir(light_setups_dir):
            print(f"Found filename: {filename}")  # Check the filename
            if filename.endswith(".blend"):
                name = os.path.splitext(filename)[0]
                blend_path = os.path.join(light_setups_dir, filename)
                preview_path = os.path.join(previews_dir, name + ".jpg")

                light_setups.append(
                    {
                        "name": name,
                        "blend_path": blend_path,
                        "preview_path": preview_path,
                    }
                )
    except Exception as e:
        print(f"Error in get_light_setups_data: {e}")  # Print the error
        return []  # Return an empty list in case of an error
    return light_setups

# -------------------------------------------------------------------
# Custom Properties
# -------------------------------------------------------------------
bpy.types.Scene.one_click_lights_current_setup = StringProperty(
    name="Current Light Setup", description="The currently selected light setup"
)


# -------------------------------------------------------------------
# UI Panel
# -------------------------------------------------------------------

class LightManagerPanel(Panel):
    bl_idname = "LIGHT_MANAGER_PT_panel"
    bl_label = "OCL"  # This is the bl_label attribute
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lighting"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Get the current light setup
        current_setup_name = scene.one_click_lights_current_setup
        light_setups = get_light_setups_data()
        current_setup = next(
            (
                setup
                for setup in light_setups
                if setup["name"] == current_setup_name
            ),
            None,
        )

        # Preview Image Block
        box = layout.box()
        box.scale_x = 1.5  # Make the box wider
        box.scale_y = 1.5  # Make the box taller

        if current_setup and os.path.exists(current_setup["preview_path"]):
            # Load the image
            image = bpy.data.images.load(current_setup["preview_path"])

            # Draw the image
            box.template_icon(icon_value=image.bindcode, scale=8)
        else:
            box.label(text="No Preview", icon="ERROR")

        # Row for selecting the light setup
        row = box.row()
        row.alignment = "CENTER"
        row.operator("light_manager.open_light_setup_popup", text="Change", icon="DOWNARROW_HLT")

        # Apply Button at the Bottom
        layout.separator()  # Add a separator line
        if current_setup:
            layout.operator("light_manager.apply_light_setup", text="Apply Light Setup")
        else:
            layout.label(text="Select a light setup first.")


# -------------------------------------------------------------------
# Operator to Apply Light Setup
# -------------------------------------------------------------------
class ApplyLightSetupOperator(Operator):
    bl_idname = "light_manager.apply_light_setup"
    bl_label = "Apply Light Setup"

    light_setup_name: StringProperty(
        name="Light Setup Name", description="Name of the light setup to apply"
    )

    def execute(self, context):
        light_setups = get_light_setups_data()
        selected_setup = None
        for setup in light_setups:
            if setup["name"] == self.light_setup_name:
                selected_setup = setup
                break

        if selected_setup:
            try:
                # Load the light setup from the .blend file
                filepath = selected_setup["blend_path"]
                with bpy.data.libraries.load(filepath) as (data_from, data_to):
                    data_to.lights = data_from.lights

                # Create a new collection for the lights
                light_collection = bpy.data.collections.new(
                    name=selected_setup["name"] + "_lights"
                )
                bpy.context.scene.collection.children.link(light_collection)

                # Add the loaded lights to the new collection
                for light in data_to.lights:
                    light_collection.objects.link(light)

                self.report({"INFO"}, f"Applied light setup: {selected_setup['name']}")

            except Exception as e:
                self.report({"ERROR"}, f"Error applying light setup: {e}")
                return {"CANCELLED"}
        else:
            self.report({"ERROR"}, "Light setup not found.")
            return {"CANCELLED"}

        return {"FINISHED"}


# -------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------
classes = [LightManagerPanel, ApplyLightSetupOperator]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)


# This allows you to run the script directly from Blender's Text Editor
# to test the add-on without installing it.
if __name__ == "__main__":
    register()