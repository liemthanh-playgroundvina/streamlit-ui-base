import base64
import uuid
from copy import deepcopy
from io import BytesIO
from PIL import Image

from datetime import datetime
import pytz
import random
import pandas as pd
import streamlit as st

from backend.generate_image import GenerateImageService

st.set_page_config(page_title="Generate Image", page_icon="🖼️")

st.markdown("""# <center>Generate Image</center>""", unsafe_allow_html=True)

# Initialize table
if "table_gen_img" not in st.session_state:
    st.session_state.table_gen_img = pd.DataFrame({
        "Time": [],
        "Mode": [],
        "Prompt": [],
        "Style": [],
        "Model": [],
        "Image Original": [],
        "Image Generated": []
    })

if "gen_img_url" not in st.session_state:
    st.session_state.gen_img_url = ""
if "gen_uploader_key" not in st.session_state:
    st.session_state.gen_uploader_key = str(uuid.uuid4())
if "seed" not in st.session_state:
    st.session_state.seed = random.randint(1, 10000)


def random_seed():
    st.session_state.seed = random.randint(1, 10000)


def get_model_name(pa_mode: str, pa_host: str):
    key_name = pa_host + " " + pa_mode
    dict_model = {
        "OpenAI Text-To-Image": ("dall-e-3", "dall-e-2"),
        "OpenAI Image-To-Image": (""),
        "Fireworks Text-To-Image": ("playground-v2-5-1024px-aesthetic", "stable-diffusion-xl-1024-v1-0", "playground-v2-1024px-aesthetic", "SSD-1B", "japanese-stable-diffusion-xl"),
        "Fireworks Image-To-Image": ("playground-v2-5-1024px-aesthetic", "stable-diffusion-xl-1024-v1-0", "playground-v2-1024px-aesthetic", "SSD-1B", "japanese-stable-diffusion-xl"),
    }
    return dict_model[key_name]


st.sidebar.header("Parameters")
with st.sidebar:
    prompt = st.text_area(label="Prompt", value="")
    mode = st.selectbox("Mode", ("Text-To-Image", "Image-To-Image"))
    if mode == "Image-To-Image":
        image_type = st.selectbox("Image Type", ("Upload File", "url"), )
        img_uploader = None
        if image_type == "url":
            st.session_state.gen_img_url = st.text_area(label="Image URL", value=st.session_state.gen_img_url).strip()
            st.markdown("_:blue-background[Limit 5MB Image]_")
            if st.session_state.gen_img_url:
                try:
                    st.image(st.session_state.gen_img_url)
                except:
                    raise ValueError("Undefined Image")
        elif image_type == "Upload File":
            img_uploader = st.file_uploader(label="Upload file", type=["jpg", "png", "tiff", "heif", "heic"],
                                            key=st.session_state.gen_uploader_key)
            if img_uploader:
                img_uploader_show = deepcopy(img_uploader)
                image = Image.open(img_uploader_show)
                st.image(image, caption="Uploaded Image", use_column_width=True)
    else:
        style = st.selectbox("Style", ("Photo", "Cartoon", "3D", "Digital Art", "Random", "Other"))
        if style == "Other":
            style = st.text_input(label="Your style name: ", value="")

    # LLMs Param
    with st.expander("Configure"):
        if mode == "Text-To-Image":
            host = st.selectbox("Host Model", ("Fireworks", "OpenAI"))
            model_name = st.selectbox("Model", get_model_name(mode, host))
            size = st.selectbox("image_size", ("1024 x 1024", "768 x 1344", "1344 x 768"))
            cfg_scale = st.slider("cfg_scale", min_value=1, max_value=100, value=7, step=1)
            seed = st.slider("seed", min_value=1, max_value=10000, value=st.session_state.seed, step=1)
            steps = st.slider("steps", min_value=1, max_value=100, value=30, step=1)
            sampler = st.selectbox("sampler", ("K_EULER", None, "K_DPMPP_2M"))
            safety_check = st.checkbox("safety_check", value=True)

            config = {
                "size": size,
                "cfg_scale": cfg_scale,
                "seed": seed,
                "steps": steps,
                "sampler": sampler,
                "safety_check": safety_check
            }

        else:
            host = st.selectbox("Host Model", ("Fireworks",))
            model_name = st.selectbox("Model", get_model_name(mode, host))
            cfg_scale = st.slider("cfg_scale", min_value=1, max_value=100, value=7, step=1)
            seed = st.slider("seed", min_value=1, max_value=10000, value=st.session_state.seed, step=1)
            steps = st.slider("steps", min_value=1, max_value=100, value=30, step=1)
            sampler = st.selectbox("sampler", ("K_EULER", None, "K_DPMPP_2M"))
            safety_check = st.checkbox("safety_check", value=True)
            init_image_mode = st.selectbox("init_image_mode", ("IMAGE_STRENGTH", "STEP_SCHEDULE"))
            if init_image_mode == "IMAGE_STRENGTH":
                image_strength = st.slider("image_strength", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
                config = {
                    "init_image_mode": init_image_mode,
                    "image_strength": image_strength,
                    "cfg_scale": cfg_scale,
                    "seed": seed,
                    "steps": steps,
                    "sampler": sampler,
                    "safety_check": safety_check
                }
            elif init_image_mode == "STEP_SCHEDULE":
                step_schedule_start = st.slider("step_schedule_start", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
                step_schedule_end = st.slider("step_schedule_end", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
                config = {
                    "init_image_mode": init_image_mode,
                    "step_schedule_start": step_schedule_start,
                    "step_schedule_end": step_schedule_end,
                    "cfg_scale": cfg_scale,
                    "seed": seed,
                    "steps": steps,
                    "sampler": sampler,
                    "safety_check": safety_check
                }

    submit = st.button("Generate")
    if submit:
        if mode == "Text-To-Image":
            image_original = ""
            style, positive_prompt, negative_prompt = GenerateImageService().gen_prompt_following_style(prompt, style)
            data_response = GenerateImageService().text_to_image(host, model_name, positive_prompt, negative_prompt, config)

        elif mode == "Image-To-Image":
            style = ""
            img_uploader_to_pred = deepcopy(img_uploader)
            if img_uploader is not None:
                img_bytes = img_uploader.read()
                img = Image.open(BytesIO(img_bytes))
                img_format = img.format.lower()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                img_base64 = f"data:image/{img_format};base64,{img_base64}"
                image_original = f'<img src="{img_base64}" alt="Uploaded Image" width="200"/>'

            else:
                image_original = f"[Here]({st.session_state.gen_img_url})"

            data_response = GenerateImageService().image_to_image(st.session_state.gen_img_url, host, model_name, prompt, "", config, img_uploader_to_pred)

            st.session_state.gen_img_url = ""
            st.session_state.gen_uploader_key = str(uuid.uuid4())

        image_generate = f"[Here]({data_response})"

        new_row = {
            "Time": [datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M:%S')],
            "Mode": [mode],
            "Prompt": [positive_prompt],
            "Style": [style],
            "Model": [model_name],
            "Image Original": [image_original],
            "Image Generated": [image_generate],
        }
        new_row = pd.DataFrame(new_row)
        df = pd.concat([new_row, st.session_state.table_gen_img], ignore_index=True)
        st.session_state.table_gen_img = df

# Convert the entire DataFrame to a Markdown string
markdown_string = st.session_state.table_gen_img.to_markdown(index=False)
st.markdown(f"""{markdown_string}""", unsafe_allow_html=True)
