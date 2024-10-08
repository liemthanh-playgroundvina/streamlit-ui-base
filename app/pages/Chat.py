import json
import re
import uuid
from copy import deepcopy
from io import BytesIO

import matplotlib.pyplot as plt

import pandas as pd
from PIL import Image
import streamlit as st

from backend.chat import ChatService, get_title
from backend.common.s3 import upload_file, S3UploadFileObject

from env import settings

st.set_page_config(page_title="Chat", page_icon="📄")

st.markdown("""# <center>Chatbot""", unsafe_allow_html=True)
st.markdown("""<center>chat & search & plot & GPTs & vision & document""", unsafe_allow_html=True)

# Initialize chat history
if "chat" not in st.session_state:
    st.session_state.chat = []
if "img_url" not in st.session_state:
    st.session_state.img_url = None
if "docs_url" not in st.session_state:
    st.session_state.docs_url = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())


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

def get_host():
    with open(settings.LLMS_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f).keys()


def get_model_name(pa_mode: str, pa_host: str):
    if pa_mode == "GPTs":
        pa_mode = "Chat"
    key_name = pa_host + " " + pa_mode
    dict_model = {
        "OpenAI Chat": ("gpt-4o", "gpt-4o-mini"),
        "OpenAI Chat-Vision": ("gpt-4o", "gpt-4o-mini"),
        "OpenAI Chat-Document": ("gpt-4o", "gpt-4o-mini"),
        "local Chat": ("qwen2-1.5b", "qwen2-7b"),
        "local Chat-Vision": ("None", "None"),
        "local Chat-Document": ("qwen2-1.5b", "qwen2-7b"),
    }
    return dict_model[key_name]


def get_max_tokens_value(model: str):
    with open(settings.LLMS_FILE_PATH, 'r', encoding='utf-8') as f:
        llms = json.load(f)

    dict_token = {}
    for models in llms.values():
        dict_token.update(models)

    return dict_token.get(model, None)

def get_stores():
    with open(settings.GPTS_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f).get("_list_store", {}).keys()

def get_store_name(tag_name: str):
    with open(settings.GPTS_FILE_PATH, 'r', encoding='utf-8') as f:
        gpts_data = json.load(f)

    tags = gpts_data.get("_list_store", {})
    return tags[tag_name]


def chat_bot(mode: str, messages: list, chat_model: dict, store_name: str = "", data_id: str = ""):
    client = ChatService().get_client(mode, messages, chat_model, store_name, data_id)

    searching_placeholder = st.empty()
    metadata_placeholder = st.empty()
    message_placeholder = st.empty()

    full_response = ""
    search = None
    plot = None
    message_placeholder.markdown(rf"""{full_response}""" + "▌")

    metadata_data = []

    for event in client.events():
        # Searching
        if event.event == "SEARCHING":
            with searching_placeholder.expander("Searching..."):
                ...
        if event.event == "SEARCHED":
            urls = json.loads(event.data)
            with searching_placeholder.expander(f"Searched {len(urls)} pages"):
                    for url in urls:
                        st.markdown(f"[{get_title(url)}]({url})")
            event.data = ""
            search = {"title": f"Searched {len(urls)} pages", "urls": [f"[{get_title(url)}]({url})" for url in urls]}

        # Metadata
        if event.event == "METADATA":
            metadata_data.extend(json.loads(event.data))

        # Response
        if event.event == "CHATTING":
            full_response += event.data.replace("<!<newline>!>", "\n")

        if event.event == "DONE":
            print(metadata_data)
            with metadata_placeholder.expander(f"Metadata"):
                for meta in metadata_data:
                    st.markdown(f"- [{meta['task']}, {meta['usage']}]")
            break

        # Plot
        if "<PLOT>" not in full_response:
            response = full_response.replace("<PLOT", "Analysing...")
            message_placeholder.markdown(rf"""{response}""")

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

    message_placeholder.markdown(rf"""{full_response}""")
    return full_response, search, plot


st.sidebar.header("Parameters")
img_url = None
with st.sidebar:
    # Mode
    mode = st.selectbox("Mode", ("Chat", "GPTs", "Chat-Vision", "Chat-Document"), on_change=reset_messages)
    if mode == "Chat":
        system_prompt = st.text_area(label="System Prompt", value="You are an assistant.")
    elif mode == "GPTs":
        tag_name  = st.selectbox("Store Name", get_stores(), on_change=reset_messages)
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
    # Chat Document
    elif mode == "Chat-Document":
        system_prompt = st.text_area(label="System Prompt", value="You are an chatbot assistant named AIHOHO created by LiemThanh.")
        chat_id = st.text_input(label="Chat ID", value="")
        type_chat = st.selectbox("Type", ("Long Context", "RAG"), on_change=reset_messages)
        # URLs
        document_urls = st.text_area(label="Document URLs", value="")
        st.markdown("_:blue-background[Limit 5MB]_")
        if document_urls:
            document_urls = [url.strip() for url in document_urls.split("\n") if url.strip()]
            st.session_state.docs_url.extend(document_urls)
        # Uploads
        uploaded_files = st.file_uploader(label="Upload multiple documents",
                                          type=["pdf", "doc", "docx", "txt", "xls", "xlsx", "csv", "ppt", "pptx", "md",
                                                "html", "xml"],
                                          accept_multiple_files=True)
        if uploaded_files is not None:
            for file in uploaded_files:
                s3_upload = S3UploadFileObject(filename=file.name, file=BytesIO(file.getvalue()), mimetype=file.type)
                upload_info = upload_file(s3_upload, "ai-center/chat-document")
                st.session_state.docs_url.append(upload_info["data"]["url"])

        if st.button("Add Documents"):
            if st.session_state.docs_url:
                data_id = ChatService().embed_docs(type_chat, st.session_state.docs_url)
                st.markdown(f"_:blue-background[Data_ID: {data_id}]_")
            else:
                raise ValueError("No Documents")
            st.session_state.docs_url = []

    # LLMs Param
    with st.expander("Configure"):
        host = st.selectbox("Host Model", get_host(), on_change=reset_messages)
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
            full_response, search_data, plot_data = chat_bot(mode, messages, config, store_name=store_name)
        elif "type_chat" in globals():
            full_response, search_data, plot_data = chat_bot(f"{mode} {type_chat}", messages, config, data_id=chat_id)

        else:
            full_response, search_data, plot_data = chat_bot(mode, messages, config)

    # Add assistant response to chat history
    st.session_state.chat.append({"role": "assistant", "content": full_response, "search": search_data, "plot": plot_data})
