import boto3
import json
import base64
from PIL import Image
import cv2
import matplotlib.pyplot as plt

#def resize(image):
#    img = Image.open(image)
#    return img.resize((384, 384))

# Load the image
def resize(img):
    
    image = cv2.imread(img)

# Get the original dimensions
    original_height, original_width = image.shape[:2]
# Calculate new dimensions
    def calculate_new_dimensions(original_width, original_height):
        # Find the nearest multiples of 64
        new_width = (original_width // 64) * 64
        new_height = (original_height // 64) * 64

        # Maintain the aspect ratio
        aspect_ratio = original_width / original_height

        # Adjust to ensure dimensions are less than or equal to 400
        if new_width > 400 or new_height > 400:
            if new_width > new_height:
                new_width = min(new_width, 400)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(new_height, 400)
                new_width = int(new_height * aspect_ratio)

        return new_width, new_height

    # Get the new dimensions
    new_width, new_height = calculate_new_dimensions(original_width, original_height)
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    # Save the resized image
    cv2.imwrite("resized_image.jpg", resized_image)
    
    return resized_image


# maintains aspect ratio
def scale(image):
    base_width = 384
    img = Image.open(image)
    wpercent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    return img


class Generator:
    def __init__(self, region_name='us-west-2'):
        self.polly = boto3.client('polly', region_name=region_name)
        self.bedrock_runtime_client = boto3.client(
            service_name='bedrock-runtime', 
            region_name=region_name
        )
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    def generate_description(self, file_path):
        try:
            with open(file_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode()

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": encoded_image
                                }
                            },
                            {
                                "type": "text",
                                "text": "Describe this garment in a way that I can use your description to edit an image of a person using Stable Diffusion XL. Make sure to insist on the main color and features. Your output will be used as input with the other model so be direct, precise, and imperative."
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "anthropic_version": "bedrock-2023-05-31"
            }

            response = self.bedrock_runtime_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                body=json.dumps(payload)
            )

            output_binary = response["body"].read()
            output_json = json.loads(output_binary)
            output = output_json["content"][0]["text"]

            return output

        except Exception as e:
            print(f"An error occurred in generate_description: {e}")
            return None

    def generate_image(self, output, person_image_path="person.jpg"):
        try:
            prompt = (
                "replace shoes with " + output
            )


            with open(person_image_path, "rb") as image_file:
                init_image = base64.b64encode(image_file.read()).decode('utf8')

            body=json.dumps({
                "imageVariationParams": {
                "images": [ init_image ],
                "text": prompt,
                "similarityStrength": 0.7 },
                "taskType": "IMAGE_VARIATION",
                "imageGenerationConfig":
                    {"cfgScale":8,
                     "seed":0,
                     "width":1024,
                     "height":1024,
                     "numberOfImages":1
                    }
                })
            
            second_payload = {
             "modelId": "amazon.titan-image-generator-v2:0",
             "contentType": "application/json",
             "accept": "application/json",
             "body": body
            }

            model_id = "amazon.titan-image-generator-v2:0"


            response = self.bedrock_runtime_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                body=body
            )

            response_body = json.loads(response.get("body").read())
            print(response_body.get('result', 'No result found in response'))

            artifacts = response_body.get("artifacts")
            if artifacts and len(artifacts) > 0:
                base64_image = artifacts[0].get("base64")
                base64_bytes = base64_image.encode('ascii')
                image_bytes = base64.b64decode(base64_bytes)

                with open("result.jpg", "wb") as binary_file:
                    binary_file.write(image_bytes)
            else:
                print("No artifacts found in response.")

        except Exception as e:
            print(f"An error occurred in generate_image: {e}")
