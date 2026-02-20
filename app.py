ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
import os
import csv
import random
from datetime import datetime

import streamlit as st
from PIL import Image  # pip install pillow

IMAGE_DIR = "images"
RESULTS_CSV = "human_ratings.csv"
EXPECTED_IMAGES = 50


def list_images():
    """
    Return a shuffled list of VALID image file paths (including subfolders).
    - Includes .jpg/.jpeg/.png/.webp
    - Filters out corrupt/non-image files (e.g., HTML saved as .jpg, 0-byte files)
    """
    exts = (".jpg", ".jpeg", ".png", ".webp")
    paths = []

    for root, _, files in os.walk(IMAGE_DIR):
        for file in files:
            if file.lower().endswith(exts):
                paths.append(os.path.join(root, file))

    # Validate images
    valid, invalid = [], []
    for p in paths:
        try:
            with Image.open(p) as im:
                im.verify()
            valid.append(p)
        except Exception:
            invalid.append(p)

    # Optional UI info (comment out if you want a super-clean UI)
    # if invalid:
    #     st.info(f"Ignored {len(invalid)} invalid/corrupt images (not counted).")

    valid = sorted(valid)
    random.shuffle(valid)
    return valid


def init_session_state(images):
    """Initialize Streamlit session state variables."""
    if "image_list" not in st.session_state:
        st.session_state.image_list = images
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if "session_id" not in st.session_state:
        st.session_state.session_id = (
            f"sess_{int(datetime.utcnow().timestamp())}_{random.randint(1000, 9999)}"
        )


def save_response(
    session_id,
    image_path,
    random_score,
    organized_score,
    messy_score,
    disorderly_score,
    fake_score,
):
    """Append one row of response to CSV."""
    os.makedirs(os.path.dirname(RESULTS_CSV) or ".", exist_ok=True)
    file_exists = os.path.isfile(RESULTS_CSV)

    with open(RESULTS_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "timestamp_utc",
                    "session_id",
                    "image_name",
                    "random_score",
                    "organized_score",
                    "messy_score",
                    "disorderly_score",
                    "fake_score",
                ]
            )
        writer.writerow(
            [
                datetime.utcnow().isoformat(),
                session_id,
                os.path.basename(image_path),
                random_score,
                organized_score,
                messy_score,
                disorderly_score,
                fake_score,
            ]
        )


def download_csv_widget():
    st.sidebar.header("Admin")

    pw = st.sidebar.text_input("Admin password", type="password")

    if not ADMIN_PASSWORD:
        st.sidebar.error("ADMIN_PASSWORD is not set in Streamlit Secrets/Env.")
        return

    if pw != ADMIN_PASSWORD:
        st.sidebar.info("Enter password to access downloads.")
        return

    st.sidebar.success("Admin access granted ✅")

    if os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV, "rb") as f:
            st.sidebar.download_button(
                label="📥 Download responses CSV",
                data=f,
                file_name="human_ratings.csv",
                mime="text/csv",
                key="admin_download_csv",
            )
    else:
        st.sidebar.warning("CSV not created yet. Submit at least one rating first.")


def main():
    st.title("HUMAN ORIENTED METHOD")
    st.write("This study is part of a Master's project.")

    # Download button (appears once at least 1 response is submitted)
    download_csv_widget()
    st.divider()

    images = list_images()
    if not images:
        st.error(f"No valid images found in folder: {IMAGE_DIR}")
        st.stop()

    # Enforce target count without crashing the app
    if len(images) != EXPECTED_IMAGES:
        st.warning(
            f"Expected {EXPECTED_IMAGES} images, but found {len(images)} valid images. "
            f"Please ensure you have exactly {EXPECTED_IMAGES} VALID images "
            f"(supported: .jpg, .jpeg, .png, .webp)."
        )
        st.stop()

    init_session_state(images)

    idx = st.session_state.idx
    if idx >= len(st.session_state.image_list):
        st.success("You have finished rating all images. Thank you for your participation!")
        download_csv_widget()  # allow download at the end
        st.stop()

    current_image = st.session_state.image_list[idx]
    image_name = os.path.basename(current_image)

    st.subheader(f"Image {idx + 1} of {len(st.session_state.image_list)}")
    st.image(current_image, use_container_width=True)

    st.markdown("### Please rate the following statements")

    likert_options = {
        "1 - Strongly disagree": 1,
        "2 - Disagree": 2,
        "3 - Neutral": 3,
        "4 - Agree": 4,
        "5 - Strongly agree": 5,
    }

    questions = {
        "random": "The content in this image is random.",
        "organized": "The content in this image is organized.",
        "messy": "The content in this image is messy.",
        "disorderly": "The content in this image is disorderly.",
        "fake": "I think this image is fake.",
    }

    # Random order of the 5 questions for each image (stable per session+image)
    question_keys = list(questions.keys())
    seed_str = f"{st.session_state.session_id}_{image_name}"
    rnd = random.Random(seed_str)
    rnd.shuffle(question_keys)

    choices = {}
    for k in question_keys:
        choices[k] = st.radio(
            questions[k],
            options=list(likert_options.keys()),
            index=2,
            key=f"{k}_{idx}",
        )

    if st.button("Submit and show next image"):
        scores = {k: likert_options[choices[k]] for k in choices}

        save_response(
            session_id=st.session_state.session_id,
            image_path=current_image,
            random_score=scores["random"],
            organized_score=scores["organized"],
            messy_score=scores["messy"],
            disorderly_score=scores["disorderly"],
            fake_score=scores["fake"],
        )

        st.session_state.idx += 1
        st.rerun()


if __name__ == "__main__":
    main()
