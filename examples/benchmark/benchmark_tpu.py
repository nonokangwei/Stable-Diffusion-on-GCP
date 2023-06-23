import torch
import torch_xla
import torch_xla.core.xla_model as xm
import time
import traceback
from diffusers import DiffusionPipeline
from diffusers import EulerAncestralDiscreteScheduler

device = xm.xla_device()

torch.nn.functional.scaled_dot_product_attention

pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",    
    # torch_dtype=torch.float16,
)
pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
# pipe = pipe.to("cuda")
pipe = pipe.to(device)

# pipe.unet = torch.compile(pipe.unet)
# pipe.enable_xformers_memory_efficient_attention()

batch_size_list = [2 ** x for x in range(0, 8)]
steps = 50
cfg_scale = 15
prompt = "postapocalyptic steampunk city, exploration, cinematic, realistic, hyper detailed, photorealistic maximum detail, volumetric light, (((focus))), wide-angle, (((brightly lit))), (((vegetation))), lightning, vines, destruction, devastation, wartorn, ruins"
negative_prompt = "(((blurry))), ((foggy)), (((dark))), ((monochrome)), sun, (((depth of field)))"

# prewarm
_ = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    num_inference_steps=20,
    num_images_per_prompt=1,
    guidance_scale=cfg_scale,
    height=512,
    width=512,
    ).images


result = []
for batch_size in batch_size_list:
    try:
        t0 = time.time()
        images = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            num_images_per_prompt=batch_size,
            guidance_scale=cfg_scale,
            height=512,
            width=512,
            ).images
        t1 = time.time()
        its = steps * batch_size / (t1 - t0)
        print("batch_size {}, it/s: {}, time: {}".format(batch_size, round(its, 2), round((t1 - t0), 2)))
    # except torch.cuda.OutOfMemoryError as e:
    #     print("batch_size {}, OOM".format(batch_size))
    #     its = 0
    except Exception:
        print(traceback.print_exc())
        print("batch_size {}, OOM".format(batch_size))
        its = 0
    result.append(round(its, 2))

print(result)

# images[0]




