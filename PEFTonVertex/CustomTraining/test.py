from inference import InferencePipeline

pipe = InferencePipeline()
image = pipe.run(base_model="runwayml/stable-diffusion-v1-5",lora_weight_name=f"/your_model_path/a photo of sks dog_lora.pt",prompt="a photo of sks dog in the forest", negative_prompt="",n_steps=50,guidance_scale=7.5, seed=1)
image.save("/your_output_path/dog.png")                              