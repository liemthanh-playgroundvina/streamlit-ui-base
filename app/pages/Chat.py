import json
import re
import uuid
from copy import deepcopy
from io import BytesIO
import matplotlib.pyplot as plt

import pandas as pd
from PIL import Image
import streamlit as st

from backend.chat import ChatBotService, ChatVisionService, get_title
from backend.common.s3 import upload_file, S3UploadFileObject

st.set_page_config(page_title="Chat", page_icon="📄")

st.markdown("""# <center>Chatbot & Chat-Vision</center>""", unsafe_allow_html=True)

# Initialize chat history
if "chat" not in st.session_state:
    st.session_state.chat = []
if "img_url" not in st.session_state:
    st.session_state.img_url = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())
if "searching" not in st.session_state:
    st.session_state.searching = False


# Display chat messages from history on app rerun
for message in st.session_state.chat:
    if message["role"] == "user":
        chat_mess = st.chat_message(message["role"], avatar="🧑🏻")
    else:
        chat_mess = st.chat_message(message["role"], avatar="🤖")
    with chat_mess:
        # Search
        search = message.get("search", None)
        if search is not None:
            with st.expander(search['title']):
                for url in search['urls']:
                    st.markdown(url)
        if isinstance(message["content"], str):
            st.markdown(rf"""{message["content"]}""")
        elif isinstance(message["content"], list):
            st.image(message["content"][1]['image_url']['url'])
            st.markdown(rf"""{message["content"][0]['text']}""")
        else:
            print(type(message["content"]))


        # Plot
        plot = message.get("plot", None)
        if plot is not None:
            data, title, xlabel, ylabel = plot['data'], plot['title'], plot['xlabel'], plot['ylabel']
            try:
                df = pd.DataFrame(data)
                try:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df.iloc[:, 0], df.iloc[:, 1], marker='o', linestyle='-', color='b')
                    ax.set_title(title)
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    ax.grid(True)
                    plt.xticks(rotation=90)
                    st.pyplot(fig)
                except:
                    st.write("Error when generate plot, this is table of plot:")
                    st.dataframe(df.style.highlight_max(axis=0))
            except:
                st.json(plot)


def reset_messages():
    st.session_state.chat = []
    pass


def get_model_name(pa_mode: str, pa_host: str):
    if pa_mode == "GPTs":
        pa_mode = "Chat"
    key_name = pa_host + " " + pa_mode
    dict_model = {
        "OpenAI Chat": ("gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"),
        "OpenAI Chat-Vision": ("gpt-4o", "gpt-4-turbo"),
        "Fireworks Chat": ("dbrx-instruct", "mixtral-8x22b-instruct", "llama-v3-70b-instruct", "llama-v3-70b-instruct-hf"),
        "Fireworks Chat-Vision": ("firellava-13b", "llava-yi-34b"),
    }
    return dict_model[key_name]


def get_store_name(tag_name: str):
    tags = {
        "Writing": ["Write For Me", "Humanizer Pro", "CV Writer", "Automated Writer", "Quality Raters SEO Guide",
                    "Cover Letter"],
        "Productive": ["Canva", "Diagrams: Show Me", "AI PDF", "Excel GPT",
                       "Presentation and Slides GPT: PowerPoints, PDFs", "Resume", "Video Maker", "Whimsical Diagrams"],
        "Research & Analysis": ["Consensus", "SciSpace", "ScholarAI", "Wolfram", "MarketingAI"],
        "Education": ["Math Mentor", "Universal Primer", "Tutor Me", "Physics", "Machine Learning", "Data Analytics",
                      "Economics Econ"],
        "Lifestyle": ["Astrology Birth Chart GPT", "Travel Guide", "Fitness, Workout & Diet - PhD Coach", "Rizz GPT",
                      "Song Maker", "DeepGame", "Books", "AutoExpert", "Personal Color Analysis"]
    }
    return tags[tag_name]


def get_max_tokens_value(model: str):
    dict_token = {
        # OpenAI (Output limit is 4096 token)
        "gpt-4o": 4096,  # 128000,
        "gpt-4-turbo": 4096,  # 128000,
        "gpt-3.5-turbo": 4096, # 16385,
        # Fireworks
        # # Chat
        "dbrx-instruct": 32768,
        "mixtral-8x22b-instruct": 65536,
        "llama-v3-70b-instruct": 8192,
        "llama-v3-70b-instruct-hf": 8192,
        # # ChatVision
        "firellava-13b": 4096,
        "llava-yi-34b": 4096,
    }
    return dict_token[model]


def chat_bot(mode: str, messages: list, chat_model: dict, store_name: str = ""):
    if mode  == "Chat-Vision":
        client = ChatVisionService().get_client(messages, chat_model)
    elif mode in ["Chat", "GPTs"]:
        client = ChatBotService().get_client(messages, chat_model, store_name)

    searching_placeholder = st.empty()
    message_placeholder = st.empty()

    full_response = ""
    search = None
    plot = None
    message_placeholder.markdown(rf"""{full_response}""" + "▌")

    for event in client.events():
        # Searching
        if '[SEARCHING]' in event.data:
            with searching_placeholder.expander("Searching..."):
                ...
        elif '[END_SEARCHING]' in event.data:
            urls = event.data.replace("[END_SEARCHING]", "")
            urls = json.loads(urls)
            with searching_placeholder.expander(f"Searched {len(urls)} pages"):
                    for url in urls:
                        st.markdown(f"[{get_title(url)}]({url})")
            event.data = ""
            search = {"title": f"Searched {len(urls)} pages", "urls": [f"[{get_title(url)}]({url})" for url in urls]}
        elif "[DONE]" in event.data:
            break

        # Plot
        if "<PLOT>" in full_response and "</PLOT>" in full_response:
            plot_data_match = re.search(r'<PLOT>(.*?)</PLOT>', full_response, re.DOTALL)
            if plot_data_match:
                plot_data_str = plot_data_match.group(1)
                plot_data = json.loads(plot_data_str, strict=False)
                data, title, xlabel, ylabel  = plot_data['data'], plot_data['title'], plot_data['xlabel'], plot_data['ylabel']
                try:
                    df = pd.DataFrame(data)
                    try:
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.plot(df.iloc[:, 0], df.iloc[:, 1], marker='o', linestyle='-', color='b')
                        ax.set_title(title)
                        ax.set_xlabel(xlabel)
                        ax.set_ylabel(ylabel)
                        ax.grid(True)
                        plt.xticks(rotation=90)
                        st.pyplot(fig)
                    except:
                        st.write("Error when generate plot, this is table of plot:")
                        st.dataframe(df.style.highlight_max(axis=0))
                except:
                    st.json(plot_data)

                plot = plot_data

            full_response = re.sub(r'<PLOT>.*?</PLOT>', '', full_response, flags=re.DOTALL)

        full_response += event.data.replace("[SEARCHING]", "").replace("[END_SEARCHING]", "").replace("[DATA_STREAMING]", "").replace("[DONE]", "").replace("[METADATA]", "").replace("<!<newline>!>", "\n")
        if "<PLOT>" not in full_response:
            response = full_response.replace("<PLOT", "Analysing...")
            message_placeholder.markdown(rf"""{response}""")

    message_placeholder.markdown(rf"""{full_response}""")
    return full_response, search, plot


st.sidebar.header("Parameters")
img_url = None
with st.sidebar:
    # Mode
    mode = st.selectbox("Mode", ("Chat", "GPTs", "Chat-Vision"), on_change=reset_messages)
    if mode == "Chat":
        system_prompt = st.text_area(label="System Prompt", value="You are an assistant.")
    elif mode == "GPTs":
        tag_name  = st.selectbox("Store Name", ("Writing", "Productive", "Research & Analysis", "Education", "Lifestyle"), on_change=reset_messages)
        store_name = st.selectbox("Store Name", get_store_name(tag_name), on_change=reset_messages)
    elif mode == "Chat-Vision":
        system_prompt = st.text_area(label="System Prompt", value="You are an assistant.")
        image_type = st.selectbox("Image Type", ("Upload File", "url"), )
        if image_type == "url":
            st.session_state.img_url = st.text_area(label="Image URL", value=st.session_state.img_url)
            st.markdown("_:blue-background[Limit 5MB Image]_")
        elif image_type == "Upload File":
            img_uploader = st.file_uploader(label="Upload file", type=["jpg", "png", "tiff"],
                                            key=st.session_state.uploader_key)
            if img_uploader is not None:
                # img_bytes = img_uploader.read()
                # img = Image.open(BytesIO(img_bytes))
                # img_format = img.format.lower()
                # img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                # st.session_state.img_url = f"data:image/{img_format};base64,{img_base64}"

                with Image.open(BytesIO(img_uploader.getvalue())) as image:
                    image_bytes = BytesIO()
                    image.save(image_bytes, format=image.format)
                    image_bytes.seek(0)

                s3_upload = S3UploadFileObject(filename=img_uploader.name, file=image_bytes, mimetype=img_uploader.type)
                upload_info = upload_file(s3_upload, "ai-center/chat-vision")
                st.session_state.img_url = upload_info["data"]["url"]

        if st.session_state.img_url:
            try:
                st.image(st.session_state.img_url)
            except:
                raise ValueError("Undefined Image")
    # LLMs Param
    with st.expander("Configure"):
        host = st.selectbox("Host Model", ("OpenAI", "Fireworks"), on_change=reset_messages)
        model_name = st.selectbox("Model", get_model_name(mode, host), on_change=reset_messages)
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
        max_tokens = st.slider("Max_tokens", min_value=256, max_value=get_max_tokens_value(model_name), value=4096, step=32)
        max_messages = st.slider("Max Messages History Chat", min_value=4, max_value=100, value=40, step=2)
        st.session_state.chat = st.session_state.chat[-max_messages:]
    st.button('Clear History Chat', on_click=reset_messages)


# Chat
if prompt := st.chat_input("Text..."):
    # Display user message
    if st.session_state.img_url:
        content = [
            {"type": "text", "text": prompt},
            { "type": "image_url", "image_url": {"url": st.session_state.img_url, "detail": "low"}}
        ]
        st.session_state.chat.append({"role": "user", "content": content})
        with st.chat_message("user", avatar="🧑🏻️"):
            st.image(st.session_state.img_url)
            st.markdown(rf"""{prompt}""")
        st.session_state.img_url = None
        st.session_state.uploader_key = str(uuid.uuid4())
    else:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑🏻️"):
            st.markdown(rf"""{prompt}""")

    # Display assistant message
    with st.chat_message("assistant", avatar="🤖"):
        messages = deepcopy(st.session_state.chat)
        if 'system_prompt' in globals():
            messages.insert(0, {"role": "system", "content": system_prompt})
        config = {
            "platform": host,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if "store_name" in globals():
            full_response, search_data, plot_data = chat_bot(mode, messages, config, store_name)
        else:
            full_response, search_data, plot_data = chat_bot(mode, messages, config, "")

    # Add assistant response to chat history
    st.session_state.chat.append({"role": "assistant", "content": full_response, "search": search_data, "plot": plot_data})
