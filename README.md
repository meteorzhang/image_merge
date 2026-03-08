# Defect Extraction and Synthesis Tool

This is a Python application built with PyQt5 for extracting defects from images and synthesizing new defect datasets.

## Features

1.  **Defect Extraction**:
    *   Load an image and its corresponding LabelMe JSON annotation file.
    *   Automatically extract defects based on polygon annotations.
    *   Crop defects to their minimum bounding rectangle.
    *   Make the background around the defect transparent.
    *   Save extracted defects as PNG images and corresponding JSON files in the `defect_library` folder, organized by defect label.

2.  **Defect Synthesis**:
    *   Load an "OK" (background) image.
    *   Browse the extracted defect library by category.
    *   Drag and drop defects onto the OK image.
    *   **Scale**: Use the mouse wheel to resize the selected defect.
    *   **Rotate**: Use 'R' (clockwise) and 'L' (counter-clockwise) keys to rotate the selected defect.
    *   **Delete**: Use the 'Delete' key to remove a selected defect.
    *   **Save**: Save the synthesized image and a new LabelMe JSON annotation file with updated coordinates.

## Installation

Ensure you have Python installed, then install the required dependencies:

```bash
pip install opencv-python numpy PyQt5
```

## Usage

1.  Run the application:
    ```bash
    python main.py
    ```

2.  **To Extract Defects**:
    *   Click `Defect Extraction` in the menu.
    *   Select the source image (e.g., in the `images/` folder).
    *   Select the corresponding LabelMe JSON file.
    *   The extracted defects will appear in the `defect_library` folder and can be viewed in the left panel.

3.  **To Synthesize Defects**:
    *   Click `Load OK Image` to load a background image.
    *   Select a defect category from the dropdown on the left.
    *   Drag and drop defect images from the list onto the main view.
    *   Adjust position, scale, and rotation as needed.
    *   Click `Save Image` to save the result in the `synthesized/` folder.

## Directory Structure

*   `main.py`: Main application entry point and UI logic.
*   `utils.py`: Helper functions for image processing and file handling.
*   `defect_library/`: Stores extracted defects (organized by label).
*   `synthesized/`: Stores generated images and annotations.
*   `images/`: Sample images (if available).
