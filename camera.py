import streamlit as st

def main():
    st.title("Webcam Photo Capture and Upload")

    # Use the camera input widget to take a picture
    picture = st.camera_input("Take a picture")

    if picture:
        # Display the captured picture
        st.image(picture)

        # Optionally, save the image to the server or process it
        with open("uploaded_image.png", "wb") as f:
            f.write(picture.getbuffer())

        st.success("Image saved successfully!")

if __name__ == "__main__":
    main()

