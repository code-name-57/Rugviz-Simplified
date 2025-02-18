from fastapi import FastAPI
from nicegui import app, ui, events
from backend import create_hero, read_hero, update_hero, delete_hero, list_heroes, create_background, list_backgrounds, update_background, delete_background, read_background
from models import Hero, RVBackground
import asyncio
import os
import pathlib
import shlex
import shutil
import subprocess
from image_transform import apply_rug_to_background
import cv2

class HeroApp:
    def __init__(self, fastapi_app: FastAPI) -> None:
        self.fastapi_app = fastapi_app

        self.setup_ui()

        ui.run_with(
            self.fastapi_app,
            mount_path='/gui',  # Optional: if omitted then @ui.page paths are at the root
            storage_secret='pick your private secret here',
        )

    

    def setup_ui(self):
        @ui.page('/backgrounds/')
        def show_backgound_list():

            def refresh_background_list():
                background_list.clear()
                for bg in list_backgrounds():
                    with background_list:
                        with ui.row().classes('items-center'):
                            ui.image(source=bg.image_path)
                            ui.button("Edit", on_click=lambda bg_id=bg.id: open_edit_dialog(bg_id)).classes("ml-2")
                            ui.button("Delete", on_click=lambda bg_id=bg.id: delete_bg(bg_id)).classes("ml-2")
                            ui.button("Render Rugs", on_click=lambda bg_id=bg.id : render_rugs(bg_id)).classes("ml-2")
            def delete_bg(bg_id: int):
                delete_background(bg_id)
                refresh_background_list()


            def open_edit_dialog(bg_id: int):
                # Retrieve current background details
                bg = None
                for item in list_backgrounds():
                    if item.id == bg_id:
                        bg = item
                        break
                if bg is None:
                    ui.notify("Background not found", color="warning")
                    return

                d = ui.dialog()
                                # Initialize annotation dictionary with existing points if present
                annotation = {}
                if getattr(bg, "point1_x", None) is not None:
                    annotation["points"] = [
                        (bg.point1_x, bg.point1_y),
                        (bg.point2_x, bg.point2_y),
                        (bg.point3_x, bg.point3_y),
                        (bg.point4_x, bg.point4_y),
                    ]
                else:
                    annotation["points"] = []
                
                with d, ui.card().classes("p-4"):
                    ui.label("Annotate the image with a rectangle")
                    # Display current image
                    annotated_image = ui.interactive_image(bg.image_path, on_mouse=lambda e: on_mouse(e, annotation), events=["mousedown", "mouseup","mousemove"])
                    
                    def on_mouse(e: events.MouseEventArguments, coords: dict):
                        # Initialize points list if not already set
                        if "points" not in coords:
                            coords["points"] = []
                        # Define a threshold to detect if a click is close enough to an existing point (in image coordinates)
                        threshold = 10

                        if e.type == "mousedown":
                            # Check if the click is near an existing point for dragging
                            for i, (px, py) in enumerate(coords["points"]):
                                if abs(e.image_x - px) < threshold and abs(e.image_y - py) < threshold:
                                    coords["drag_index"] = i
                                    break
                            else:
                                # If no nearby point found and we have less than 4 points, add a new one
                                if len(coords["points"]) < 4:
                                    coords["points"].append((e.image_x, e.image_y))
                                    ui.notify(f"Point {len(coords['points'])} added", color="primary")
                                else:
                                    ui.notify("Already 4 points set.", color="warning")
                        
                        elif e.type == "mousemove":
                            # If dragging an existing point, update its coordinates continuously.
                            if "drag_index" in coords:
                                idx = coords["drag_index"]
                                coords["points"][idx] = (e.image_x, e.image_y)
                        
                        elif e.type == "mouseup":
                            if "drag_index" in coords:
                                ui.notify(f"Point {coords['drag_index']+1} moved", color="primary")
                                del coords["drag_index"]

                        update_svg(coords)

                    def update_svg(coords: dict):
                        points = coords.get("points", [])
                        svg_elements = '<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">'
                        
                        # Draw circles for each point.
                        for (x, y) in points:
                            svg_elements += f'<circle cx="{x}" cy="{y}" r="5" fill="red" />'
                        
                        # Draw lines connecting the points in order.
                        if len(points) > 1:
                            for i in range(len(points) - 1):
                                x1, y1 = points[i]
                                x2, y2 = points[i+1]
                                svg_elements += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="blue" stroke-width="2" />'
                            
                            # If 4 points, close the polygon.
                            if len(points) == 4:
                                x1, y1 = points[-1]
                                x2, y2 = points[0]
                                svg_elements += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="blue" stroke-width="2" />'
                                
                                # Create a mask using the drawn polygon.
                                polygon_points = " ".join(f"{x},{y}" for x, y in points)
                                svg_elements += f'''
                                    <defs>
                                      <mask id="mask">
                                        <rect x="0" y="0" width="100%" height="100%" fill="white" />
                                        <polygon points="{polygon_points}" fill="black" />
                                      </mask>
                                    </defs>
                                    <rect x="0" y="0" width="100%" height="100%" fill="rgba(0,0,0,0.5)" mask="url(#mask)" />
                                '''
                        svg_elements += '</svg>'
                        annotated_image.content = svg_elements
                    
                    ui.button("Save Annotation", on_click=lambda: save_edited(bg_id, annotation, d)).classes("mt-2")
                d.open()
            
            def save_edited(bg_id: int, coords: dict, dialog):
                bg_old_obj = read_background(bg_id)
                if "points" in coords and len(coords["points"]) == 4:
                    # Extract the four points
                    p1, p2, p3, p4 = coords["points"]
                    # Update the background record with the coordinate values
                    new_background = RVBackground.model_validate({
                        "id": bg_id,
                        "image_path": bg_old_obj.image_path,
                        "point1_x": int(p1[0]), "point1_y": int(p1[1]),
                        "point2_x": int(p2[0]), "point2_y": int(p2[1]),
                        "point3_x": int(p3[0]), "point3_y": int(p3[1]),
                        "point4_x": int(p4[0]), "point4_y": int(p4[1]),
                    })
                    update_background(background_id=bg_id, background=new_background)
                    ui.notify("Background updated", color="positive")
                    dialog.close()
                    refresh_background_list()
                else:
                    ui.notify("Please annotate by selecting four points.", color="warning")
            
            async def handle_upload(args: events.UploadEventArguments):
                if 'image' in args.type:
                    # Handle image file uploads
                    os.makedirs('data', exist_ok=True)
                    os.chdir('data')
                    os.chdir('backgrounds')
                    with open(args.name, 'wb') as f:
                        f.write(args.content.read())
                    # Update the interactive image to the newly uploaded image.
                    background_obj = RVBackground.model_validate({'image_path': f'/data/backgrounds/{args.name}'})
                    create_background(background_obj)

                    ui.notify("Image uploaded successfully.", color="positive")
                    os.chdir('../..')
                    upload.run_method('reset')
                    refresh_background_list()

            async def render_rugs(bg_id: int):
                bg = read_background(bg_id)
                if not bg:
                    ui.notify("Background not found", color="warning")
                    return
                if None in (bg.point1_x, bg.point1_y, bg.point2_x, bg.point2_y, bg.point3_x, bg.point3_y, bg.point4_x, bg.point4_y):
                    ui.notify("Background annotation incomplete", color="warning")
                    return
                homography_points = [
                    [bg.point1_x, bg.point1_y],
                    [bg.point2_x, bg.point2_y],
                    [bg.point3_x, bg.point3_y],
                    [bg.point4_x, bg.point4_y]
                ]
                if not bg:
                    ui.notify("Background not found", color="warning")
                    return
                background_image_path = bg.image_path
                print(f"PATH ::: {background_image_path}")
                if background_image_path.startswith('/data/'):
                    # Convert the NiceGUI URL to a local filesystem path for OpenCV
                    background_image_path = os.path.join(os.getcwd(), background_image_path.lstrip('/'))
                rugs_root = os.path.join("data", "rugs")
                output_base = os.path.join("data", "output", f"background_{bg_id}")

                # Read the background image to determine its dimensions then compute default homography points.
                bg_img = cv2.imread(background_image_path)
                if bg_img is None:
                    ui.notify("Could not read background image", color="warning")
                    return
                (h, w) = bg_img.shape[:2]

                for root, _, files in os.walk(rugs_root):
                    for file in files:
                        if file.lower().endswith((".jpg", ".png")):
                            rug_path = os.path.join(root, file)
                            relative = os.path.relpath(root, rugs_root)
                            dest_dir = os.path.join(output_base, relative)
                            os.makedirs(dest_dir, exist_ok=True)
                            output_file = os.path.join(dest_dir, file)
                            rug_img = cv2.imread(rug_path)
                            rendered_img = apply_rug_to_background(bg_img, rug_img, homography_points)
                            cv2.imwrite(output_file, rendered_img)

                ui.notify("Rugs rendered successfully.", color="positive")

            os.makedirs('data', exist_ok=True)
            app.add_static_files('/data', 'data')

            # build UI elements first
            ui.label("Background Images List").classes('text-h5')
            with ui.column().classes('w-full items-center'):
                ui.label('Extract images from video').classes('text-3xl m-3')
                upload = ui.upload(label='pick a video file', auto_upload=True, on_upload=handle_upload)
                results = ui.row().classes('w-full justify-center mt-6')
                background_list = ui.column()

            refresh_background_list()


# Usage/initialization example:
def init(fastapi_app: FastAPI) -> None:
    HeroApp(fastapi_app)