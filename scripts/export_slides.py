import os
import win32com.client

def export_pptx_slides(pptx_path, output_dir):
    abs_pptx = os.path.abspath(pptx_path)
    abs_out = os.path.abspath(output_dir)
    os.makedirs(abs_out, exist_ok=True)

    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    # Open presentation read-only, without window
    presentation = powerpoint.Presentations.Open(abs_pptx, WithWindow=False)

    try:
        # SaveAs with format 17 = ppSaveAsPNG
        presentation.SaveAs(abs_out, 17)
        print(f"Exported slides to: {abs_out}")
    finally:
        presentation.Close()
        powerpoint.Quit()

if __name__ == "__main__":
    export_pptx_slides("DeploySafe_Midterm_Presentation.pptx", "docs/slides_preview")
