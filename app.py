import os
import csv
import random
from datetime import datetime

import streamlit as st

# Folder that contains the study images
IMAGE_DIR = "images"          # inside this, you have images/real and images/fake
# File where we store responses
RESULTS_CSV = "human_ratings.csv"


def list_images():
    """Return a shuffled list of image file paths (including subfolders)."""
    paths = []

    # Walk through images/, including images/real and images/fake
    for root, dirs, files in os.walk(IMAGE_DIR):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                paths.append(os.path.join(root, file))

    paths = sorted(paths)
    random.shuffle(paths)
    return paths


def init_session_state(images):
    """Initialize Streamlit session state variables."""
    if "image_list" not in st.session_state:
        st.session_state.image_list = images
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if "session_id" not in st.session_state:
        # simple session id: timestamp + random int
        st.session_state.session_id = (
            f"sess_{int(datetime.utcnow().timestamp())}_{random.randint(1000, 9999)}"
        )


def save_response(session_id, image_path, random_score, organized_score):
    """Append one row of response to CSV."""
    # Ensure directory exists (for relative paths)
    os.makedirs(os.path.dirname(RESULTS_CSV) or ".", exist_ok=True)
    file_exists = os.path.isfile(RESULTS_CSV)

    with open(RESULTS_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["timestamp_utc", "session_id", "image_name", "random_score", "organized_score"]
            )
        writer.writerow(
            [
                datetime.utcnow().isoformat(),
                session_id,
                os.path.basename(image_path),
                random_score,
                organized_score,
            ]
        )


def main():
    st.title("HUMAN ORIENTED METHOD")

    st.write(
        """
        This study is part of a Master's project on fake image detection.

        For each image:

        - Please rate how **random** the image appears.
        - Please rate how **organized** the image appears.

        Use the scale:

        1 = Strongly disagree  
        2 = Disagree  
        3 = Neutral  
        4 = Agree  
        5 = Strongly agree  

        There are no right or wrong answers. Thank you for your help!
        """
    )

    images = list_images()
    if not images:
        st.error(f"No images found in folder: {IMAGE_DIR}")
        return

    init_session_state(images)

    idx = st.session_state.idx
    if idx >= len(st.session_state.image_list):
        st.success("You have finished rating all images. Thank you for your participation!")
        st.stop()

    current_image = st.session_state.image_list[idx]

    st.subheader(f"Image {idx + 1} of {len(st.session_state.image_list)}")
    st.image(current_image, use_container_width=True)

    st.markdown("### Please rate the following statements")

    # Likert-style options
    likert_options = {
        "1 - Strongly disagree": 1,
        "2 - Disagree": 2,
        "3 - Neutral": 3,
        "4 - Agree": 4,
        "5 - Strongly agree": 5,
    }

    random_choice = st.radio(
        "This image is random.",
        options=list(likert_options.keys()),
        index=2,  # default to neutral
        key=f"random_{idx}",
    )
    organized_choice = st.radio(
        "This image is organized.",
        options=list(likert_options.keys()),
        index=2,
        key=f"organized_{idx}",
    )

    if st.button("Submit and show next image"):
        random_score = likert_options[random_choice]
        organized_score = likert_options[organized_choice]

        save_response(
            session_id=st.session_state.session_id,
            image_path=current_image,
            random_score=random_score,
            organized_score=organized_score,
        )

       
        st.session_state.idx += 1
        st.rerun()  


if __name__ == "__main__":
    main()
