import bpy
import os

class TEXTURE_OT_AutoCorrectMaps(bpy.types.Operator):
    """Auto-correct texture map names to match SOP standards"""
    bl_idname = "texture.auto_correct_maps"
    bl_label = "Auto Correct Maps"
    bl_description = "Correct texture map names to SOP standards (basecolor, normal, etc.)"

    SOP_MAPS = {
        "basecolor": [
            "basecolor", "diff", "diffuse", "albedo", "col", "clr", "color", "base",
            "basecolour", "base_color", "base_colour", "diffuse_color", "diff_col",
            "base_col", "colr", "base_color_map", "diffuse_map", "albedo_map"
        ],
        "roughness": [
            "roughness", "rough", "rgh", "rghnss", "rghness", "rghn", "roughnessmap",
            "rough_map", "rgh_map", "rghmap", "rough_map", "roughness_map", "rgh_map"
        ],
        "specular": [
            "specular", "spec", "spr", "specularcolor", "specular_col", "spec_col",
            "spec_map", "specular_map", "specular_color", "spec_map", "specular_map"
        ],
        "metallic": [
            "metallic", "met", "metal", "metalness", "met_map", "metal_map",
            "metallic_map", "metal_map", "metalness_map"
        ],
        "normal": [
            "normal", "nrm", "norm", "nmrm", "normalmap", "normal_map", "norm_map",
            "nmap", "bump", "bump_map", "normal_bump", "nrm_map", "normal_bump_map",
            "bump_normal", "normal_bump_map"
        ],
        "height": [
            "height", "hgt", "heightmap", "height_map", "hgt_map", "elevation",
            "elevation_map", "bump_height", "height_map", "hmap", "displacement",
            "disp", "displacementmap", "disp_map", "displace", "displace_map",
            "height_disp", "displacement_map", "height_displacement", "disp_map"
        ],
        "alpha": [
            "alpha", "alp", "a", "opa", "opacity", "transparency", "transp", "mask",
            "mask_map", "alpha_mask", "transp_map", "opacity_map"
        ],
        "ao": [
            "ao", "occlusion", "occl", "ambientocclusion", "ambient_occlusion", "ao_map",
            "occlusion_map", "occl_map", "amb_occl", "occlusion_map", "aochannel",
            "ao_channel", "ambientocclusion_map", "occlusion_map", "occl_map", "ao_map",
            "ao_mask", "occlusion_mask", "ao_alpha", "ao_transparency"
        ],
    }

    def execute(self, context):
        corrected = 0
        skipped = 0

        synonym_to_sop = {}
        for sop_name, synonyms in self.SOP_MAPS.items():
            for synonym in synonyms:
                synonym_to_sop[synonym.lower()] = sop_name

        for img in bpy.data.images:
            if img.source != 'FILE' or img.library:
                skipped += 1
                continue

            original_name = img.name
            name_without_ext = os.path.splitext(original_name)[0]
            parts = name_without_ext.split('_')

            if len(parts) < 2:
                skipped += 1
                continue

            map_index = -1
            sop_name = None

            for i, part in enumerate(parts):
                normalized = part.lower().strip()
                if normalized in synonym_to_sop:
                    map_index = i
                    sop_name = synonym_to_sop[normalized]
                    break

            if map_index >= 0:
                parts[map_index] = sop_name
                new_name_without_ext = '_'.join(parts)
                _, ext = os.path.splitext(original_name)
                new_name = f"{new_name_without_ext}{ext}"

                if new_name != original_name:
                    img.name = new_name
                    corrected += 1
                    self.report({'INFO'}, f"Corrected: '{original_name}' -> '{new_name}'")
                else:
                    skipped += 1
            else:
                skipped += 1

        self.report({'INFO'}, f"Maps corrected: {corrected}, Skipped: {skipped}")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(TEXTURE_OT_AutoCorrectMaps)


def unregister():
    bpy.utils.unregister_class(TEXTURE_OT_AutoCorrectMaps)
