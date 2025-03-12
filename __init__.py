bl_info = {
    "name": "Auto Merge PNG to PDF",
    "author": "80nk",
    "version": (1, 3, 1),
    "blender": (4, 3, 0),
    "location": "Output properies menu",
    "description": "Automatically merges rendered PNG files into a compressed PDF after rendering.",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}

import bpy
import os
import sys
import subprocess
import datetime
# -----------------------------------------
# Dependency Check & Installation
# -----------------------------------------
def ensure_modules():
    """Ensure Pillow and ReportLab are installed. Return True if successful."""
    try:
        import PIL
        import reportlab
        return True
    except ImportError:
        python_exe = sys.executable
        try:
            subprocess.check_call([python_exe, "-m", "ensurepip"])
            subprocess.check_call([python_exe, "-m", "pip", "install", "--user", "Pillow", "reportlab"])
            print("Dependencies installed.")
            # Re-import after installation
            import PIL
            import reportlab
            return True
        except Exception as e:
            print(f"Installation failed: {e}")
            return False

# Defer imports until dependencies are confirmed
if not ensure_modules():
    raise ImportError("Required dependencies (Pillow, ReportLab) are missing.")

from PIL import Image
from reportlab.pdfgen import canvas

from bpy.app.handlers import persistent

from . import debug

debug.log_info("Addon initialized.")

def merge_png_to_pdf(output_pdf_path, image_folder, compression_quality):
    """Merge PNG images into a compressed PDF."""
    
    """Debug Strings"""
    
    debug.log_debug("Starting merge_png_to_pdf function.")
    debug.log_variable("output_pdf_path", output_pdf_path)
    debug.log_variable("compression_quality", compression_quality)
    
    print(f"Looking for PNGs in: {image_folder}")
    
    if not os.path.exists(image_folder):
        print(f"Directory does not exist: {image_folder}")
        return
    
    images = sorted(
        [f for f in os.listdir(image_folder) if f.endswith(".png")],
        key=lambda x: os.path.getmtime(os.path.join(image_folder, x))
    )
    
    if not images:
        print("No PNG files found in the directory.")
        return
    
    print(f"Found PNG images: {images}")
    
    first_image = Image.open(os.path.join(image_folder, images[0]))
    img_width, img_height = first_image.size
    
    c = canvas.Canvas(output_pdf_path, pagesize=(img_width, img_height))
    
    processed_images = set()
    for img_file in images:
        img_path = os.path.join(image_folder, img_file)
        if img_file in processed_images:
            continue
        processed_images.add(img_file)
        print(f"Adding {img_path} to PDF with compression quality {compression_quality}")
        
        img = Image.open(img_path)
        img = img.convert("RGB")
        img = img.resize((img_width, img_height), Image.LANCZOS)
        temp_path = os.path.join(image_folder, f"temp_{img_file}.jpg")
        img.save(temp_path, "JPEG", quality=compression_quality)
        
        c.drawImage(temp_path, 0, 0, width=img_width, height=img_height)
        c.showPage()
        os.remove(temp_path)
    
    c.save()
    print(f"PDF successfully saved at: {output_pdf_path}")
	
@persistent
def auto_merge_after_render(scene, depsgraph):
    """Automatically merge rendered PNGs into a compressed PDF after rendering."""
    debug.log_debug("Starting auto_merge_after_render.")
    if not bpy.context.scene.auto_merge_png_to_pdf:
        debug.log_debug("Auto merge is disabled. Skipping.")
        return
    try:
        blend_file_path = bpy.path.abspath("//")
        pdf_folder = os.path.join(blend_file_path, "PDF")
        os.makedirs(pdf_folder, exist_ok=True)
    
        pdf_filename = bpy.context.scene.auto_merge_pdf_name.strip()
        if not pdf_filename:
            pdf_filename = "merged_output"
    
        date_str = datetime.datetime.now().strftime("%d_%m_%Y")
        counter = 1
        original_pdf_filename = f"{pdf_filename}_{date_str}.pdf"
        pdf_filename = original_pdf_filename
        while os.path.exists(os.path.join(pdf_folder, pdf_filename)):
            pdf_filename = f"{original_pdf_filename.rsplit('.', 1)[0]}_{counter}.pdf"
            counter += 1
    
        pdf_output_path = os.path.join(pdf_folder, pdf_filename)
        render_output_dir = bpy.path.abspath(bpy.context.scene.render.filepath)
        compression_quality = bpy.context.scene.auto_merge_compression_quality
    
        print(f"Render output directory: {render_output_dir}")
        print(f"PDF will be saved as: {pdf_output_path}")
    
        if not os.path.exists(render_output_dir):
            print(f"Render output directory does not exist: {render_output_dir}")
            return
    
        merge_png_to_pdf(pdf_output_path, render_output_dir, compression_quality)
		
		# Open the folder where the PDF is saved
        if os.name == 'nt':  # Windows
            subprocess.Popen(f'explorer /select,"{pdf_output_path}"')
        elif os.name == 'posix':  # macOS and Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', '-R', pdf_output_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', os.path.dirname(pdf_output_path)])
    except Exception as e:
        debug.log_error("Error in auto_merge_after_render.")
        debug.log_exception(e)

class RENDER_PT_AutoMergePDF(bpy.types.Panel):
    """Creates a panel in the render settings"""
    bl_label = "Auto Merge PNG to PDF"
    bl_idname = "RENDER_PT_auto_merge_pdf"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "auto_merge_png_to_pdf")
        layout.prop(context.scene, "auto_merge_pdf_name", text="PDF Name")
        layout.prop(context.scene, "auto_merge_compression_quality", text="Compression Quality")
        layout.prop(context.scene, "debug_mode", text="Debug Mode")
classes = (
    RENDER_PT_AutoMergePDF,
)
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    debug.log_info("Registering addon.")
    bpy.types.Scene.debug_mode = bpy.props.BoolProperty(
        name="Debug Mode",
        description="Enable debug mode for detailed logging",
        default=False
    )
    bpy.types.Scene.auto_merge_png_to_pdf = bpy.props.BoolProperty(
        name="Auto Merge PNG to PDF",
        description="Automatically merge rendered PNGs into a compressed PDF after rendering",
        default=False
    )
    bpy.types.Scene.auto_merge_pdf_name = bpy.props.StringProperty(
        name="PDF File Name",
        description="Name of the generated PDF file",
        default="merged_output"
    )
    bpy.types.Scene.auto_merge_compression_quality = bpy.props.IntProperty(
        name="Compression Quality",
        description="Quality of images in the PDF (1-100, higher is better)",
        default=90,
        min=1,
        max=100
    )  
	
    bpy.app.handlers.render_complete.append(auto_merge_after_render)
    debug.log_info("Render_complete handler appended")
   
        
def unregister():

    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
        
    debug.log_info("Unregistering addon.")
    del bpy.types.Scene.auto_merge_png_to_pdf
    del bpy.types.Scene.debug_mode
    del bpy.types.Scene.auto_merge_pdf_name
    del bpy.types.Scene.auto_merge_compression_quality
    bpy.app.handlers.render_complete.clear()
    debug.log_info("Render_complete handler removed")
        
if __name__ == "__main__":
    register()