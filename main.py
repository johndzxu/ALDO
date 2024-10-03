import streamlit as st
import io

from PIL import Image

from generator import Generator, resize


def main():
    st.title("Looks")
    
    shoes_image = "boots.jpg"

    person_image = st.camera_input("Take a picture of the person")

    if shoes_image and person_image:
        st.image(shoes_image, caption='ALDO Shoes', use_column_width=True)
        st.image(person_image, caption='Captured Person Image', use_column_width=True)

        resized_image = resize(person_image)
        resized_image.save('resized_image.jpg', format='JPEG')

        generator = Generator()
        description = generator.generate_description(shoes_image)
        if description:
            generator.generate_image(description, "resized_image.jpg")
            st.success("Image saved successfully!")

            # Display the result image
            result_image = Image.open("result.jpg")
            st.image(result_image, caption='Result Image', use_column_width=True)
        else:
            st.error("Failed to generate description.")
    else:
        st.warning("Please upload a garment image and take a picture of the person.")

if __name__ == "__main__":
    main()