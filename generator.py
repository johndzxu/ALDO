import boto3
import json
import base64
from PIL import Image


def resize(image):
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
                """From the description of the garment below, 
                edit this picture so the person wears it.
                "PLEASE DO NOT CHANGE THE PERSON'S FACE!!!
                Make sure the color matches the description: """ + output
            )


            with open(person_image_path, "rb") as image_file:
                init_image = base64.b64encode(image_file.read()).decode('utf8')

            body = json.dumps({
                "text_prompts": [{"text": prompt}],
                "init_image": init_image
            })

            model_id = "stability.stable-diffusion-xl-v1"

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

                print("hi")
                with open("result.jpg", "wb") as binary_file:
                    binary_file.write(image_bytes)
            else:
                print("No artifacts found in response.")

        except Exception as e:
            print(f"An error occurred in generate_image: {e}")