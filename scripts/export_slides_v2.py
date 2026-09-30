import os
import sys
import win32com.client

def export_pptx_slides(pptx_path, output_dir):
    abs_pptx = os.path.abspath(pptx_path)
    abs_out = os.path.abspath(output_dir)
    os.makedirs(abs_out, exist_ok=True)

    print(f"Opening PowerPoint for: {abs_pptx}")
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    # Open presentation in read-only / minimized mode
    presentation = powerpoint.Presentations.Open(abs_pptx, WithWindow=False)

    try:
        slide_count = presentation.Slides.Count
        print(f"Total slides found: {slide_count}")
        # ppSaveAsJPG = 17
        presentation.SaveAs(abs_out, 17)
        print(f"Slides exported successfully to: {abs_out}")
    finally:
        presentation.Close()
        powerpoint.Quit()

if __name__ == "__main__":
    pptx_file = sys.argv[1] if len(sys.argv) > 1 else "DeploySafe_Midterm_Presentation_v2.pptx"
    out_folder = sys.argv[2] if len(sys.argv) > 2 else "docs/slides_preview_v2"
    export_pptx_slides(pptx_file, out_folder)
