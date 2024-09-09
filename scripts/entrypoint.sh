#!/bin/bash

python scripts/add_llm.py

streamlit run app/Home.py --server.port "${BASE_PORT}" --server.maxUploadSize 5
